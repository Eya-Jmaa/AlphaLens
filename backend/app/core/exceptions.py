"""Custom Exceptions"""


class FinAgentException(Exception):
    """Base exception for FinAgent"""
    pass


class ConfigurationException(FinAgentException):
    """Configuration error"""
    pass


class LLMException(FinAgentException):
    """LLM provider error"""
    pass


class DatabaseException(FinAgentException):
    """Database error"""
    pass


class APIException(FinAgentException):
    """External API error"""
    pass