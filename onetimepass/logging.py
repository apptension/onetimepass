import functools
import logging

from onetimepass import settings

"""Example usage:
```
from onetimepass.logging import logger

logger.debug("Hello World")
```
"""

logging_basic_config = functools.partial(
    logging.basicConfig,
    format="[%(asctime)s] %(levelname)s:%(module)s:%(lineno)d: %(message)s",
    level=settings.DEFAULT_LOG_LEVEL,
)

logger = logging.getLogger(__name__)
