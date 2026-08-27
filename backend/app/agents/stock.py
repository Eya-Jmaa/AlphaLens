"""Stock Analysis Agent with Real Data"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.services.cache_service import CacheService
from app.services.company_service import CompanyService

logger = logging.getLogger(__name__)


class StockAnalysisAgent(BaseAgent):
    """Stock Analysis Agent with real financial data"""
    
    def __init__(
        self,
        llm_provider,
        company_service: CompanyService = None,
        cache_service: CacheService = None
    ):
        super().__init__("StockAnalysis", llm_provider)
        self.company_service = company_service or CompanyService(cache_service)
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform stock analysis with real data"""
        tickers = state.get("tickers", [])
        self.logger.info(f"Analyzing stocks: {tickers}")

        if not tickers:
            return {"errors": ["No tickers to analyze"]}

        analysis_results = []
        technical_results: Dict[str, Any] = {}
        errors: List[str] = []

        for ticker in tickers:
            try:
                # Get real company data
                company_data = await self.company_service.get_company_info(ticker)

                # Get market data with technical analysis
                market_data = await self.company_service.get_market_data(ticker)

                # Generate analysis with LLM
                analysis = await self._analyze_company(ticker, company_data, market_data)

                analysis_results.append({
                    "ticker": ticker,
                    "company_data": company_data,
                    "market_data": market_data,
                    "analysis": analysis,
                })
                technical_results[ticker] = market_data.get("technical", {})

            except Exception as e:
                self.logger.error(f"Failed to analyze {ticker}: {e}")
                errors.append(f"Stock analysis failed for {ticker}: {str(e)}")

        self.logger.info(f"Completed analysis for {len(analysis_results)} stocks")

        return {
            "stock_analysis_results": analysis_results,
            "technical_analysis_results": technical_results,
            "errors": errors,
        }
    
    async def _analyze_company(
        self,
        ticker: str,
        company_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate detailed analysis using LLM with real data"""
        
        # Format the data for the prompt
        info = company_data
        tech = market_data.get("technical", {})
        returns = market_data.get("returns", {})
        
        # Format numbers safely
        def format_number(value, default="N/A"):
            if value is None:
                return default
            if isinstance(value, (int, float)):
                if abs(value) > 1_000_000_000:
                    return f"${value/1_000_000_000:,.2f}B"
                elif abs(value) > 1_000_000:
                    return f"${value/1_000_000:,.2f}M"
                elif abs(value) > 1_000:
                    return f"${value:,.0f}"
                return f"{value:.2f}"
            return value
        
        prompt = f"""
        Analyze the following real financial data for {ticker}:
        
        COMPANY OVERVIEW:
        Name: {info.get('name', 'N/A')}
        Sector: {info.get('sector', 'N/A')}
        Industry: {info.get('industry', 'N/A')}
        Country: {info.get('country', 'N/A')}
        
        VALUATION:
        Market Cap: {format_number(info.get('market_cap'))}
        P/E Ratio: {info.get('pe_ratio', 'N/A')}
        EPS: ${info.get('eps', 'N/A')}
        Dividend Yield: {info.get('dividend_yield', 'N/A')}
        
        PRICE DATA:
        Current Price: ${info.get('price', 'N/A')}
        Previous Close: ${info.get('previous_close', 'N/A')}
        Day High: ${info.get('day_high', 'N/A')}
        Day Low: ${info.get('day_low', 'N/A')}
        Volume: {info.get('volume', 'N/A')}
        Avg Volume: {info.get('avg_volume', 'N/A')}
        52-Week High: ${info.get('fifty_two_week_high', 'N/A')}
        52-Week Low: ${info.get('fifty_two_week_low', 'N/A')}
        
        TECHNICAL INDICATORS:
        SMA 20: {tech.get('sma_20', 'N/A')}
        SMA 50: {tech.get('sma_50', 'N/A')}
        SMA 200: {tech.get('sma_200', 'N/A')}
        RSI: {tech.get('rsi', 'N/A')}
        ATR: {tech.get('atr', 'N/A')}
        
        PRICE CHANGES:
        1 Day: {tech.get('price_change', {}).get('1d', 'N/A')}%
        1 Week: {tech.get('price_change', {}).get('1w', 'N/A')}%
        1 Month: {tech.get('price_change', {}).get('1m', 'N/A')}%
        3 Months: {tech.get('price_change', {}).get('3m', 'N/A')}%
        1 Year: {tech.get('price_change', {}).get('1y', 'N/A')}%
        
        RISK METRICS:
        Volatility (Annual): {returns.get('volatility', 'N/A')}
        Sharpe Ratio: {returns.get('sharpe_ratio', 'N/A')}
        Max Drawdown: {returns.get('max_drawdown', 'N/A')}
        VaR 95%: {market_data.get('risk', {}).get('var_95', 'N/A')}
        
        Based on this REAL data, provide a comprehensive analysis with:
        1. Company Overview and Business Model
        2. Financial Health Assessment
        3. Valuation Analysis (is it over/undervalued?)
        4. Technical Analysis Summary
        5. Growth Prospects
        6. Key Strengths
        7. Key Risks and Challenges
        8. Overall Investment Outlook
        
        Be specific and reference the actual numbers provided.
        """
        
        system_prompt = """You are a senior financial analyst with expertise in fundamental and technical analysis.
        Provide objective, data-driven analysis based on the real financial data provided.
        Be specific about the numbers and what they indicate.
        Do not invent information not present in the data.
        """
        
        response = await self.call_llm(prompt, system_prompt)
        
        # Try to parse as JSON
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        return {
            "analysis": response,
            "ticker": ticker,
            "status": "text_analysis",
            "timestamp": datetime.now().isoformat(),
        }
