# todo

```
logging motor pulse:
really, just a count + timestamp every few seconds would be enough
actually, maybe two counts
one for forward ticks and one for backward ticks
i think it should be easy to detect the problem, if it exists at this layer.  if i remember right, it was like 8% fast
or some huge number
```

## Worth mentioning

- Integrates with [Gphoto2/libgphoto2](https://github.com/gphoto/gphoto2)
- [Exiftool](https://github.com/exiftool/exiftool) integration automatically stores the weather, temperature, moon cycle, target object, RA/DEC, geolocation, etc... directly into the EXIF meta data on each image taken
- [Wttr](https://github.com/chubin/wttr.in) for weather information

<br/><br/>

## Camera (gphoto2)

### - Get settings

`GET` | `/api/camera/config/`

### - Update settings

```json
POST | /api/camera/config
{
  "iso": "800",
  "aperture": "3.5",
  "shutterspeed": "30"
}
```

### - Set Lens

```json
POST | 5/api/lens/55/ {}
```

### - Capture Light Frame

TODO

### - Capture Dark Frame

TODO

### - Capture Flat Frame

TODO

### - Capture Bias Frame

TODO

## Fully 3D-Printed, Equatorial Mount and extras

- mount
- filters
- manual => auto focuser knob stepper

Add info, links to files, etc...
<br/><br/>

# Web Application

- Live
- control camera, View photos, dew heater, peripherals
- control photography sessions, start/end time
- capture calibration frames
- plate solving
- astrometry.net integration
- histogram evaluation
- precalculated template photoshoots with suggested settings (perhaps show sample photo from last photoshoot)
- what's visible in my sky now - links to slew to them and capture photos
- calendar of events
- Calibration frame wizard, step checklist

<br/>
<br/>

# The Build

- Telescope Pier
- Housing for Raspberry Pi
- Dew Heater
- BOM
- Celestron Nexstar 6SE
- Canon T2I
- etc...
