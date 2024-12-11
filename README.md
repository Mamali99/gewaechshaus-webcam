#  thin-edge.io Webcam Stream plugin

This plugin of thinedge io pulls data from an connected webcam and pushes them to the binary store of Cumulocity IoT. 
It is triggerd by the custom c8y_Startstream operation and pushes one frame every 30 seconds, as long as defined in the timeout_minutes parameter in the operation call.

To use on a device that runs thin-edge.io, a plugin of the operation plugin concept is used. The tedge_agent is checking for c8y_Startstream operation and is triggering the particular plugin. 

Tested with Rasperry Pi Zero 2 W and USB Webcam Lenovo HD 500. 

## Requirements

- Working thin-edge.io installation ([thinedge. io installation](https://thin-edge.github.io/thin-edge.io/install/))
- Python3 and pip3 installation (will not work on python2)


## Installation 

1. Clone this repo on the thin-edge.io device
2. run sudo -H pip3 install -r requirements.txt from this Startstream directory
3. Copy c8y_Startstream to the following directory "/etc/tedge/operations/c8y/"
4. Copy c8y_Startstream.py to the following directory "/bin/"
5. Make sure, that both files do have permissions for beeing executed by tedge_mapper ("chmod 644 c8y_Startstream and chmod 555 c8y_Startstream.py")
6. Add tedge to video user group (reboot required): 
```shell
sudo adduser tedge video
sudo usermod -a -G video tedge
```
7. Create a SmartRest2.0 rule, via Cumulocity IoT UI as follows, to be able to trigger the plugin:
    - ID: `greenhousewebcam`
    - Response ID: `541`
    - Name: `c8y_Startstream`
    - Base pattern: -
    - Condition: `c8y_Startstream`
    - Patterns:
        - `deviceId`
        - `c8y_Startstream.parameters.timeout_minutes`
8. Register the template on thin-edge
```shell
sudo tedge config set c8y.smartrest.templates greenhousewebcam
```

## Usage

Make sure thin-edge.io is connected to Cumulocity. 
If installation is done properly according to the steps above, you hae to disconnect and reconnect thin-edge.io. In that way the supported Operations will be updated.

```shell
sudo tedge disconnect c8y
sudo tedge connect c8y
```

However it would also to be sufficient to restart the tedge_mapper service via e.g.:

```shell
sudo systemctl tedge_mapper restart
```

Then create the operation via REST API:
 ```shell
curl --location '<url>/devicecontrol/operations/' \
--header 'Authorization: Basic <base64(tenantid/username:password>)' \
--header 'Content-Type: application/json' \
--header 'Accept: application/vnd.com.nsn.cumulocity.operation+json;' \
--data '{
  "deviceId" : "29883285",
  "c8y_Startstream": {
    "parameters": {
      "timeout_minutes": "5"
    }
  },
  "description": "Start the stream"
 ```


## ToDo
- Use credentials provided by thin-edge or bearer token, insted of credentials in code.
- Settings (eg. FPS)  via config-file (editable via c8y with thinedge)
