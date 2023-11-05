import logging

from . import taffylib

logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class Taffy:
    def __init__(self) -> None:
        self.__ptr = taffylib.init()
        logger.debug("init() -> %s", self.__ptr)
        self._use_rounding: bool = True

        # These are used to track pointers and verify that unreferenced nodes and styles are also dropped in Taffy
        # self._nodes: set[int] = set()
        # self._styles: set[int] = set()

    def __del__(self) -> None:
        if self.__ptr is None:
            return

        # taffylib.node_drop_all(self._ptr)
        # for ptr in self._styles:
        #     logger.warn("style_drop(%s)", ptr)
        #     taffylib.style_drop(ptr)
        # for ptr in self._nodes:
        #     logger.warn("node_drop(%s)", ptr)
        #     taffylib.node_drop(self._ptr, ptr)

        taffylib.free(self.__ptr)
        logger.debug("free(ptr: %s)", self.__ptr)
        self.__ptr = None

    @property
    def _ptr(self) -> int:
        return self.__ptr

    @property
    def use_rounding(self) -> bool:
        return self._use_rounding

    @use_rounding.setter
    def use_rounding(self, value: bool) -> None:
        # if value == self._use_rounding:
        #     return
        if value:
            taffylib.enable_rounding(self._ptr)
        else:
            taffylib.disable_rounding(self._ptr)
        self._use_rounding = value
