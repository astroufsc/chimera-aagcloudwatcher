import datetime
import logging
import sys
from astropy import units
from chimera.instruments.weatherstation import WeatherBase
from chimera.interfaces.weatherstation import WeatherTemperature, WeatherSafety, WSValue, WeatherTransparency  # , WeatherRain

log = logging.getLogger(__name__)

if sys.platform == "win32":
    sys.coinit_flags = 0
    from win32com.client import Dispatch
    import pythoncom
else:
    log.warning("Not on Windows. COM+ AAG cloud watcher plugin won't work.")


class AAGCloudWatcherCOM(WeatherBase, WeatherTemperature, WeatherSafety, WeatherTransparency):
    __config__ = dict(
        model="AAGWare Cloud Watcher",
        transparency_zero = 36,
        transparency_temp_close = -25,
        transparency_factor = 3.2,
    )

    def __init__(self):
        WeatherBase.__init__(self)

    def __start__(self):
        """
        Start AAG Cloud Watcher software
        """
        self.log.debug("Starting AAGCloudWatcherCOM")
        _ocw = Dispatch("AAG_CloudWatcher.CloudWatcher")
        _ocw.Device_Start()
        self._ocwStream = pythoncom.CreateStreamOnHGlobal()
        # Multi-thread COM method calls trick based on:
        # http://stackoverflow.com/questions/22863646/marshaling-com-objects-between-python-processes-using-pythoncom
        pythoncom.CoMarshalInterface(self._ocwStream,
                                     pythoncom.IID_IDispatch,
                                     _ocw._oleobj_,
                                     pythoncom.MSHCTX_LOCAL,
                                     pythoncom.MSHLFLAGS_TABLESTRONG)
        _ocw = None

    def __stop__(self):
        self._ocwStream.Seek(0, 0)
        pythoncom.CoReleaseMarshalData(self._ocwStream)

    def temperature(self, unit_out=units.Celsius):
        pythoncom.CoInitialize()
        self._ocwStream.Seek(0, 0)
        _ocw = Dispatch(pythoncom.CoUnmarshalInterface(self._ocwStream, pythoncom.IID_IDispatch))
        ret = WSValue(datetime.datetime.utcnow(),
                      self._convert_units(_ocw.AmbientTemperature(), units.Celsius, unit_out), unit_out)
        self._ocwStream.Seek(0, 0)
        pythoncom.CoUninitialize()
        return ret

    def isRaining(self):
        pythoncom.CoInitialize()
        self._ocwStream.Seek(0, 0)
        _ocw = Dispatch(pythoncom.CoUnmarshalInterface(self._ocwStream, pythoncom.IID_IDispatch))
        ret = _ocw.Condition_Rain() > 1
        self._ocwStream.Seek(0, 0)
        pythoncom.CoUninitialize()
        return ret

    def sky_transparency(self, unit_out=units.pct):
        pythoncom.CoInitialize()
        self._ocwStream.Seek(0, 0)
        _ocw = Dispatch(pythoncom.CoUnmarshalInterface(self._ocwStream, pythoncom.IID_IDispatch))
        transp = (self["transparency_temp_close"]-_ocw.SkyTemperature())*self["transparency_factor"]+self["transparency_zero"]
        ret = WSValue(datetime.datetime.utcnow(),
                       self._convert_units(transp, units.pct, unit_out), unit_out)
        self._ocwStream.Seek(0, 0)
        pythoncom.CoUninitialize()
        return ret

    def okToOpen(self):
        """
        If there is no data available since 300 seconds ago, it is not okay to open the dome.
        """
        pythoncom.CoInitialize()
        self._ocwStream.Seek(0, 0)
        _ocw = Dispatch(pythoncom.CoUnmarshalInterface(self._ocwStream, pythoncom.IID_IDispatch))
        ret = _ocw.Safe() if _ocw.SecondsSinceGoodData() < 300 else False
        self._ocwStream.Seek(0, 0)
        pythoncom.CoUninitialize()
        return ret


    def getMetadata(self, request):
        # Temperature
        temp = self.temperature()
        return [('METTEMP', str(temp.value), ('[%s] Weather station temperature' % temp.unit))]