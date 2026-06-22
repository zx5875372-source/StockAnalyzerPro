class FinMindError(Exception):
    pass


class FinMindAPIError(FinMindError):
    pass


class FinMindRateLimitError(FinMindAPIError):
    pass


class FinMindAuthenticationError(FinMindAPIError):
    pass
