"""Error taxonomy returned as redacted, machine-readable API errors."""


class HarnessError(Exception):
    code = "HARNESS_ERROR"


class ForbiddenTool(HarnessError):
    code = "FORBIDDEN_TOOL"


class InvalidToolArguments(HarnessError):
    code = "INVALID_TOOL_ARGUMENTS"


class ToolExecutionFailed(HarnessError):
    code = "TOOL_EXECUTION_FAILED"


class ModelProtocolError(HarnessError):
    code = "MODEL_PROTOCOL_ERROR"


class LimitExceeded(HarnessError):
    code = "LIMIT_EXCEEDED"


class DeadlineExceeded(HarnessError):
    code = "DEADLINE_EXCEEDED"
