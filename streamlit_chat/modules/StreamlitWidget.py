from enum import Enum

class ExtendedEnum(Enum):

    @classmethod
    def list(cls):
        return [c.value for c in cls]

class Slider_label_visiability(ExtendedEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    COLLAPSED = "collapsed"