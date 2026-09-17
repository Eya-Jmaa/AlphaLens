"""Custom Exceptions"""


class AlphaLensException(Exception):
    """Base exception for AlphaLens"""
    pass


class ConfigurationException(AlphaLensException):
    """Configuration error"""
    pass


class LLMException(AlphaLensException):
    """LLM provider error"""
    pass


class DatabaseException(AlphaLensException):
    """Database error"""
    pass


class APIException(AlphaLensException):
    """External API error"""
    pass