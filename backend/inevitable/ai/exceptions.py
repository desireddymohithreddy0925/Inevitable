class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass

class AIProviderTimeout(AIProviderError):
    """Raised when the AI provider times out."""
    pass

class AIProviderRateLimit(AIProviderError):
    """Raised when the AI provider rate limits the request."""
    pass

class AIProviderAuthenticationError(AIProviderError):
    """Raised when authentication fails."""
    pass
