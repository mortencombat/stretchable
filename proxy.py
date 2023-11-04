from attrs import define
from icecream import ic


class Renderer:
    def __init__(self, data, coordinate_ref, elevation_ref) -> None:
        self._data = data
        self._coordinate_ref = coordinate_ref
        self._elevation_ref = elevation_ref

    def __enter__(self):
        proxy_service.start(self._data)
        transformation_service.lock(self._coordinate_ref, self._elevation_ref)

    def __exit__(self, exc_type, exc_val, exc_tb):
        proxy_service.stop()
        transformation_service.unlock()


class DataProxyService:
    def __init__(self) -> None:
        self._running = False
        self._data = None
        self._classes = []
        self._attributes = dict()

    def start(self, data):
        if self._running:
            raise Exception("DataProxyService is already in use")
        self._running = True
        self._data = data

    def stop(self):
        self._running = False
        self._data = None

    def register_class(self, cls: type):
        self._classes.append(cls)
        ic("register_class", cls)
        # TODO: discover public class attrs by inspection
        self._attributes[cls] = []

    def register_attribute(self, cls: type, name: str):
        self._attributes[cls].append(name)
        ic("register_attribute", cls, name)

    @property
    def is_active(self) -> bool:
        return self._running


class TransformationService:
    def __init__(self) -> None:
        self._locked = False
        self._coordinate_ref = None
        self._elevation_ref = None

    def lock(self, coordinate_ref, elevation_ref):
        if self._locked:
            raise Exception("TransformationService is already locked / in use")
        self._locked = True
        self._coordinate_ref = coordinate_ref
        self._elevation_ref = elevation_ref

    def unlock(self):
        self._locked = False

    @property
    def coordinate_ref(self):
        return self._coordinate_ref

    @property
    def elevation_ref(self):
        return self._elevation_ref

    @property
    def is_locked(self) -> bool:
        return self._locked


def register(cls):
    # Decorator to register a class with the DataProxyService

    proxy_service.register_class(cls)
    return cls


def require(*args):
    # Decorator to inject options and/or variables as arguments to a method, and
    # make the method behave like a read-only property.

    def inner(f):
        # Resolve *args to values and pass them into f

        class Property:
            def __get__(self, obj, cls):
                # Insert args into f
                return f(obj)

        # Return a descriptor object to make it behave like a read-only property.
        return Property()

    return inner


def derivedproperty(cls: type, name: str):
    # Decorator to 'attach' a method to a class registered with the
    # DataProxyService. `self` will be injected as the single argument, unless
    # this is combined with the @require decorator to inject additional
    # arguments.

    # This should

    def inner(f):
        return f

    proxy_service.register_attribute(cls, name)
    return inner


@define
class Option:
    arg_name: str
    locator: str


@define
class Variable:
    arg_name: str
    max_dist_hor: float
    preprocessing: str


proxy_service = DataProxyService()
transformation_service = TransformationService()


# Define a data entity class. Pre-defined data entities would be a part of
# sweco.geodata eg. not intended to be modified by the user.
@register
@define
class CPTMeasurement:
    depth: float
    qc: float
    fs: float
    u2: float

    @require(Option("k_qc", "cpt.constants.k_qc"))
    def qc_corrected(self, k1=1.2):
        return self.qc * k1


m = CPTMeasurement(2, 5.5, 0.1, 50)
ic(m.qc_corrected)


# This attaches a 'virtual' property to the CPTMeasurement class, when the
# CPTMeasurement class is accessed through the DataProxyService. This is akin to
# an extension of the class, and allows the user to add new properties to a data
# entity without modifying the class itself or having to subclass it.
@require(Variable("qc", max_dist_hor=0.5, preprocessing="average"))
@derivedproperty(CPTMeasurement, "qc_smoothed")
def _(qc):
    return qc


data = "some_data"
coordinate_ref = "S34S"
elevation_ref = "DVR90"

ic(proxy_service.is_active, transformation_service.is_locked)

with Renderer(data, coordinate_ref, elevation_ref) as renderer:
    ic("Render starting...")

    ic(proxy_service.is_active, transformation_service.is_locked)

    ic("Render completed.")


ic(proxy_service.is_active, transformation_service.is_locked)

"""
TODO:
  - The @require and @derivedproperty decorators should work together, eg. you
    can have a case with just one or with both of them. The end result should be
    a property (descriptor) that is registered with DPS, either explicitly
    through the @derivedproperty decorator or implicitly through the @register
    decorator on the class.
"""
