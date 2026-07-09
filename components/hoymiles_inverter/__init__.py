import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor, text_sensor
from esphome import pins
from esphome.const import CONF_ID, CONF_PASSWORD, CONF_SSID, CONF_TIME_ID, CONF_UPDATE_INTERVAL

# ESPHome Best Practice: Namespace definieren
hoymiles_inverter_ns = cg.esphome_ns.namespace('hoymiles_inverter')
HoymilesPlatform = hoymiles_inverter_ns.class_('HoymilesPlatform', cg.Component)

# Konfigurationsvariablen
CONF_HOYMILES_INVERTER_ID = "hoymiles_inverter_id"
CONF_INVERTERS = "inverters"
CONF_PINS = "pins"

CONF_SDIO = "sdio"
CONF_CLK = "clk"
CONF_CS = "cs"
CONF_FCS = "fcs"
CONF_GPIO2 = "gpio2"
CONF_GPIO3 = "gpio3"

# ESPHome Best Practice: Konfigurations-Schema definieren
PINS_SCHEMA = cv.Schema({
    cv.Required(CONF_SDIO): pins.internal_gpio_input_pin_schema,
    cv.Required(CONF_CLK): pins.internal_gpio_output_pin_schema,
    cv.Required(CONF_CS): pins.internal_gpio_output_pin_schema,
    cv.Required(CONF_FCS): pins.internal_gpio_output_pin_schema,
    cv.Optional(CONF_GPIO2): pins.internal_gpio_input_pin_schema,
    cv.Optional(CONF_GPIO3): pins.internal_gpio_input_pin_schema,
})

INVERTER_SCHEMA = cv.Schema({
    cv.Required("serial"): cv.string,
    cv.Optional("limit_percent"): cv.use_id(sensor.Sensor),
    cv.Optional("limit_absolute"): cv.use_id(sensor.Sensor),
    cv.Optional("reachable"): cv.use_id(text_sensor.TextSensor),
})

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(HoymilesPlatform),
    cv.Required(CONF_PINS): PINS_SCHEMA,
    cv.Required(CONF_INVERTERS): cv.ensure_list(INVERTER_SCHEMA),
    cv.Optional(CONF_UPDATE_INTERVAL, default="60s"): cv.update_interval,
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    # 1. Pins registrieren und der C++ Klasse übergeben
    pins_config = config[CONF_PINS]
    
    sdio = await cg.gpio_pin_expression(pins_config[CONF_SDIO])
    clk = await cg.gpio_pin_expression(pins_config[CONF_CLK])
    cs = await cg.gpio_pin_expression(pins_config[CONF_CS])
    fcs = await cg.gpio_pin_expression(pins_config[CONF_FCS])
    
    gpio2 = await cg.gpio_pin_expression(pins_config[CONF_GPIO2]) if CONF_GPIO2 in pins_config else None
    gpio3 = await cg.gpio_pin_expression(pins_config[CONF_GPIO3]) if CONF_GPIO3 in pins_config else None

    # Ruft die neue init_cmt Funktion in deiner cpp auf
    cg.add(var.set_pins(sdio, clk, cs, fcs, gpio2, gpio3))

    # 2. Inverter registrieren
    for inv_config in config[CONF_INVERTERS]:
        serial = inv_config["serial"]
        cg.add(var.add_inverter(serial))
        # Hier könntest du zukünftig noch die Sensor-Ids (limit_percent etc.) übergeben

    # =========================================================================
    # ESPHOME BEST PRACTICES: Bibliotheken festpinnen (Freezing)
    # =========================================================================
    
    # OpenDTU auf eine stabile, bekannte Version pinnen
    cg.add_library("tbnobody/OpenDTU", "v24.2.12")
    
    # Sub-Abhängigkeiten von OpenDTU manuell auflösen und pinnen, um 
    # den berüchtigten "Frozen" FileNotFoundError zu umgehen
    cg.add_library("jgromes/RadioLib", "7.7.1")
    cg.add_library("DaveGamble/cJSON", "1.7.18")
    cg.add_library("cesanta/Frozen", None, "https://github.com/cesanta/frozen.git")

    # Dem Compiler sagen, dass er die OpenDTU Header global finden kann
    cg.add_build_flag("-I.pio/libdeps/hoymiles-meanwell-eth-gateway/OpenDTU/lib/Hoymiles/src")
    cg.add_build_flag("-I.pio/libdeps/hoymiles-meanwell-eth-gateway/OpenDTU/lib/Hoymiles/src/radio")
    
    # NRF Support abschalten, um Kompilierungszeit zu sparen und Fehler zu vermeiden
    cg.add_build_flag("-DHOYMILES_RADIO_NRF=0")
