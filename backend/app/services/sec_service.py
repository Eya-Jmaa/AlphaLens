"""SEC EDGAR Service with Rate Limiting"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from app.config.settings import settings

logger = logging.getLogger(__name__)


class SECService:
    """Service for interacting with SEC EDGAR with rate limiting"""
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.user_agent = settings.SEC_USER_AGENT or "AlphaLens Research Platform contact@alphalens.dev"
        self.session = None
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests
        self._init_session()
    
    def _init_session(self):
        """Initialize HTTP session"""
        self.session = requests.Session()
        # No hardcoded Host header: this session hits both www.sec.gov (CIK
        # lookup, filing documents) and data.sec.gov (submissions JSON API).
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
    
    async def _rate_limit(self):
        """Ensure we don't exceed SEC rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    async def get_recent_filings(
        self,
        ticker: str,
        limit: int = 5,
        filing_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent SEC filings for a ticker with rate limiting"""
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K"]
        
        try:
            await self._rate_limit()
            
            # Get CIK from ticker
            cik = await self._get_cik(ticker)
            if not cik:
                logger.warning(f"Could not find CIK for {ticker}")
                return []
            
            # Get recent filings
            filings = await self._get_filings(cik, filing_types, limit)
            if not filings:
                logger.warning(
                    f"SEC EDGAR returned 0 filings of types {filing_types} for {ticker} (CIK {cik})"
                )
            return filings
            
        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            return []
    
    async def _get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK for a ticker"""
        try:
            # Search for company
            url = f"{self.base_url}/cgi-bin/browse-edgar"
            params = {
                "action": "getcompany",
                "CIK": ticker,
                "type": "",
                "dateb": "",
                "owner": "exclude",
                "count": 40,
            }
            
            response = self.session.get(url, params=params, timeout=20)

            # Handle rate limiting
            if response.status_code == 503:
                logger.warning(f"SEC.gov rate limit hit for {ticker}. Try again later.")
                return None
            
            response.raise_for_status()
            
            # Parse CIK from response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find CIK in the page
            cik_element = soup.find("input", {"name": "CIK"})
            if cik_element and cik_element.get("value"):
                return cik_element["value"].zfill(10)
            
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                logger.warning(f"SEC.gov rate limit hit for {ticker}. Try again later.")
            else:
                logger.error(f"Failed to get CIK for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get CIK for {ticker}: {e}")
            return None
    
    async def _get_filings(
        self,
        cik: str,
        filing_types: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get filings for a CIK via SEC's structured submissions JSON API
        (https://data.sec.gov/submissions/CIK##########.json) - the modern,
        officially-recommended replacement for scraping the legacy
        cgi-bin/browse-edgar HTML/XML output, and the only reliable way to get
        each filing's actual primary document filename."""
        try:
            await self._rate_limit()

            cik_padded = str(cik).zfill(10)
            url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

            response = self.session.get(url, timeout=15)

            if response.status_code == 503:
                logger.warning("SEC.gov rate limit hit. Waiting...")
                await asyncio.sleep(2)
                return []

            response.raise_for_status()
            data = response.json()

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            company_name = data.get("name")
            cik_unpadded = str(int(cik_padded))  # Archives URLs use no leading zeros

            filings = []
            for i, form in enumerate(forms):
                if form not in filing_types:
                    continue

                accession = recent.get("accessionNumber", [None] * len(forms))[i]
                primary_doc = recent.get("primaryDocument", [None] * len(forms))[i]
                if not accession or not primary_doc:
                    continue

                accession_nodash = accession.replace("-", "")

                filings.append({
                    "cik": cik,
                    "filing_type": form,
                    "filing_date": recent.get("filingDate", [None] * len(forms))[i],
                    "accession_number": accession,
                    "company_name": company_name,
                    "url": f"{self.base_url}/Archives/edgar/data/{cik_unpadded}/{accession_nodash}/{primary_doc}",
                })

                if len(filings) >= limit:
                    break

            return filings

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 503:
                logger.warning("SEC.gov rate limit hit. Waiting...")
                await asyncio.sleep(2)
            else:
                logger.error(f"Failed to get filings for CIK {cik}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get filings for CIK {cik}: {e}")
            return []
    
    async def get_filing_text(self, filing_url: str) -> Optional[str]:
        """Get text content of a filing"""
        try:
            await self._rate_limit()
            
            response = self.session.get(filing_url, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script/style elements, plus modern filings' inline-XBRL
            # tagging metadata (a huge <ix:header> block of hidden taxonomy
            # references that isn't part of the readable filing text, and any
            # other explicitly display:none elements used to carry XBRL facts).
            for tag in soup(["script", "style", "ix:header"]):
                tag.decompose()
            try:
                for hidden in soup.select('[style*="display:none"], [style*="display: none"]'):
                    hidden.decompose()
            except Exception:
                pass  # CSS selector support varies by parser backend; text is still usable without this


            # Get text
            text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to get filing text: {e}")
            return None