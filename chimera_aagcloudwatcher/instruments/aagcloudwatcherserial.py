import datetime
import logging

import numpy as np
import serial
from astropy import units
from chimera.instruments.weatherstation import WeatherBase
from chimera.interfaces.weatherstation import WeatherTemperature, WSValue, \
    WeatherTransparency  # , WeatherRain

log = logging.getLogger(__name__)


class AAGCloudWatcherSerial(WeatherBase, WeatherTemperature, WeatherTransparency):
    __config__ = dict(
        model="AAGWare Cloud Watcher",
        device='/dev/ttyS0',
        # Temperature correction coefficients:
        k1=33,
        k2=0,
        k3=4,
        k4=100,
        k5=100,
        # sky condition limits
        limit_clear=-25,
        limit_cloudy=-20,
        limit_overcast=30,
        # rain limits
        limit_dry=2300,
        limit_wet=1700,
        limit_rain=400,
        # luminosity limits
        limit_dark=2100,
        limit_light=6,
        limit_verylight=0
    )

    def __init__(self):
        WeatherBase.__init__(self)
        self._serial = None

        # Temperatures of IR sensor and IR measurement are converted to degC
        #		by dividing by 100.
        #
        # A! - Device name
        # B! - Firmware version
        # K! - serial number
        # T! - Ambient temperature (/100 to get value)
        # S! - IR sky temperature (/100 to get value)
        # E! - Rain frequency (2560=dry, <2560=wet, single drop = 2300)
        # C! - LDR voltage + Rain sensor temp (!4=1022 = dark, !4=11 = bright - around sunset starts to increase, seen from home)
        # D! - Device errors

        self._cmds = ('T!', 'E!', 'S!', 'C!')
        self._rets = ('!2', '!R', '!1', '!6')
        self._data = {cmd: list() for cmd in self._cmds}
        self._data_update = {cmd: list() for cmd in self._cmds}

    def __start__(self):
        """
        Start AAG Cloud Watcher serial connection
        """
        self.log.debug("Starting AAGCloudWatcherSerial")
        self.open()

    def __stop__(self):
        """
        """
        self._serial.close()

    def open(self):
        self._serial = serial.Serial(self["device"], baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1)
        self._serial.flush()
        self.setHz(1 / 60.)

    def control(self):
        for i_cmd in range(len(self._cmds)):
            self._serial.write('%s' % self._cmds[i_cmd])
            line = self._serial.readlines()[-1]
            if line[:2] == self._rets[i_cmd]:
                self.log.debug('Updating %s: "%s"' % (self._cmds[i_cmd], line))
                self._data[self._cmds[i_cmd]] = [int(v[1:]) for v in line[2:].split('!')]  # [:-1]
                self._data_update[self._cmds[i_cmd]] = datetime.datetime.utcnow()
            else:
                self.log.warning('Unexpected return of "%s": "%s". Expected was: "%s", got "%s"' % (
                    self._cmds[i_cmd], line, self._rets[i_cmd], line[:2]))
                # self.update_data(line)
        self.log.debug('Control done.')

        self.log.debug('TT: %s' % str(self.ambient_temperature()[0]))
        self.log.debug('SS: %s' % str(self.sky_temperature()[0]))
        self.log.debug('SS2: %s' % str(self.sky_temperature_corrected()[0]))

        return True

    def ambient_temperature(self):
        return self._data['T!'][0] / 100., self._data_update['T!']

    def sky_temperature(self):
        return self._data['S!'][0] / 100., self._data_update['S!']

    def sky_temperature_corrected(self):
        skyT, last_update = self.sky_temperature()
        ambT, _ = self.ambient_temperature()
        Tc = ((self['k1'] / 100.) * (ambT - self['k2'] / 10.)) + (self['k3'] / 100.) * pow(
            (np.exp(self['k4'] / 1000. * ambT)), (self['k5'] / 100.))
        return skyT - Tc, last_update

    def temperature(self, unit_out=units.Celsius):
        ambT, last_update = self.ambient_temperature()
        return WSValue(last_update, self._convert_units(ambT, units.Celsius, unit_out), unit_out)

    def sky_transparency(self, unit_out=units.pct):
        skyT, last_update = self.sky_temperature_corrected()
        if skyT < self["limit_clear"]:
            transparency = 100
        elif skyT < self["limit_overcast"]:
            transparency = 33
        else:
            transparency = 0
        return WSValue(last_update, self._convert_units(transparency, units.pct, unit_out), unit_out)

    # def isRaining(self):
    #     return self._data['frequency_rain']

    def getMetadata(self, request):
        # Temperature
        temp = self.temperature()
        return [('METTEMP', str(temp.value), ('[%s] Weather station temperature' % temp.unit)),
                ('SKYTEMP', str(self.sky_temperature_corrected()[0]), '[deg_C] Corrected sky temperature')]
