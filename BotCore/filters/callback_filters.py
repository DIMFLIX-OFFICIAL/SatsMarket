from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery
from typing import Union, List


class CData(BaseFilter):
    def __init__(self, cdata: Union[str, List[str]]):
        self.cdata = cdata

    async def __call__(self, callback: CallbackQuery) -> bool:
        if type(self.cdata) == str:
            return callback.data == self.cdata

        elif type(self.cdata) == list:
            for i in self.cdata:
                if callback.data == i:
                    return True

            return False


class CDataStart(BaseFilter):
    def __init__(self, cdata_start: Union[str, List[str]]):
        self.cdata_start = cdata_start

    async def __call__(self, callback: CallbackQuery) -> bool:
        if type(self.cdata_start) == str:
            return callback.data.endswith(self.cdata_start)

        elif type(self.cdata_start) == list:
            for i in self.cdata_start:
                if callback.data.startswith(i):
                    return True

            return False


class CDataEnd(BaseFilter):
    def __init__(self, cdata_end: Union[str, List[str]]):
        self.cdata_end = cdata_end

    async def __call__(self, callback: CallbackQuery) -> bool:
        if type(self.cdata_end) == str:
            return callback.data.endswith(self.cdata_end)

        elif type(self.cdata_end) == list:
            for i in self.cdata_end:
                if callback.data.endswith(i):
                    return True

            return False
