"""Document Chunking Service"""
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Service for chunking documents"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.separators = [
            "\n\n",  # Paragraph break
            "\n",    # Line break
            ". ",    # Sentence
            ", ",    # Clause
            " ",     # Word
        ]
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping chunks
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
        
        Returns:
            List of chunk dictionaries
        """
        if not text or len(text) < self.min_chunk_size:
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # Try different separators
        for separator in self.separators:
            if separator in text:
                chunks = self._chunk_with_separator(text, separator)
                if chunks:
                    break
        
        # If no chunks found, fallback to character-based chunking
        if not chunks:
            chunks = self._chunk_by_characters(text)
        
        # Add metadata and indices
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_length": len(chunk_text),
            }
            result.append({
                "text": chunk_text,
                "metadata": chunk_metadata,
                "chunk_id": f"{metadata.get('doc_id', 'unknown')}_{i}",
            })
        
        return result
    
    def _chunk_with_separator(
        self,
        text: str,
        separator: str
    ) -> List[str]:
        """Chunk text using a separator"""
        sections = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for section in sections:
            # If adding this section exceeds chunk size, save current chunk
            if len(current_chunk) + len(section) + len(separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Keep overlap
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + separator + section
                else:
                    current_chunk = section
            else:
                if current_chunk:
                    current_chunk += separator + section
                else:
                    current_chunk = section
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Filter chunks that are too small
        chunks = [c for c in chunks if len(c) >= self.min_chunk_size]
        
        return chunks
    
    def _chunk_by_characters(self, text: str) -> List[str]:
        """Fallback: chunk by characters"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
        return chunks
    
    def chunk_filing(
        self,
        text: str,
        filing_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk an SEC filing with specific metadata
        
        Args:
            text: Filing text
            filing_metadata: Metadata about the filing
        """
        # Try to split by sections
        sections = self._extract_sections(text)
        
        chunks = []
        for section_name, section_content in sections.items():
            if len(section_content) < self.min_chunk_size:
                continue
            
            section_metadata = {
                **filing_metadata,
                "section": section_name,
            }
            
            section_chunks = self.chunk_text(
                section_content,
                metadata=section_metadata
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from SEC filing"""
        sections = {}
        
        # Common SEC filing section headers. The (?!\s{0,3}\d) guard skips
        # table-of-contents hits, where the heading is immediately followed by
        # a page number (e.g. "Risk Factors12") rather than real section prose.
        section_patterns = {
            "risk_factors": r"ITEM 1A\.\s*RISK FACTORS(?!\s{0,3}\d)",
            "business": r"ITEM 1\.\s*BUSINESS(?!\s{0,3}\d)",
            "management": r"ITEM 10\.\s*DIRECTORS, EXECUTIVE OFFICERS AND CORPORATE GOVERNANCE(?!\s{0,3}\d)",
            "executive_compensation": r"ITEM 11\.\s*EXECUTIVE COMPENSATION(?!\s{0,3}\d)",
            "financial_statements": r"ITEM 8\.\s*FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA(?!\s{0,3}\d)",
            "management_discussion": r"ITEM 7\.\s*MANAGEMENT'S DISCUSSION AND ANALYSIS(?!\s{0,3}\d)",
            "market_risk": r"ITEM 7A\.\s*QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK(?!\s{0,3}\d)",
            "controls": r"ITEM 9A\.\s*CONTROLS AND PROCEDURES(?!\s{0,3}\d)",
            "legal_proceedings": r"ITEM 3\.\s*LEGAL PROCEEDINGS(?!\s{0,3}\d)",
            "properties": r"ITEM 2\.\s*PROPERTIES(?!\s{0,3}\d)",
        }
        
        # Find sections using regex
        remaining_text = text
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, remaining_text, re.IGNORECASE)
            if match:
                # Extract content up to next section
                next_sections = list(section_patterns.values())
                for next_pattern in next_sections:
                    if next_pattern != pattern:
                        next_match = re.search(next_pattern, remaining_text[match.start()+len(match.group()):], re.IGNORECASE)
                        if next_match:
                            content = remaining_text[match.start():match.start()+len(match.group())+next_match.start()]
                            sections[section_name] = content
                            remaining_text = remaining_text[match.start()+len(match.group())+next_match.start():]
                            break
                else:
                    # If no next section, take rest
                    sections[section_name] = remaining_text[match.start():]
                    break
        
        # If no sections found, just use the whole text
        if not sections and len(text) > 100:
            sections["full_text"] = text
        
        return sections