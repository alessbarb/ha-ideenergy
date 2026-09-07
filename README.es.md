# i-DE (Iberdrola Distribución) Custom Integration for Home Assistant

<!-- Home Assistant badges -->
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![hassfest validation](https://github.com/ldotlopez/ha-ideenergy/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/ldotlopez/ha-ideenergy/actions/workflows/hassfest.yml)
[![HACS validation](https://github.com/ldotlopez/ha-ideenergy/workflows/Validate%20with%20HACS/badge.svg)](https://github.com/ldotlopez/ha-ideenergy/actions/workflows/hacs.yml)

<!-- Code and releases -->
![GitHub Release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/ldotlopez/ha-ideenergy?include_prereleases)
[![CodeQL](https://github.com/ldotlopez/ha-ideenergy/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/ldotlopez/ha-ideenergy/actions/workflows/codeql-analysis.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Integración de [ideenergy](https://github.com/ldotlopez/ideenergy) para [Home Assistant](https://home-assistant.io/).

Esta integración proporciona datos energéticos para clientes de la distribuidora eléctrica española [i-DE](https://i-de.es).

La integración requiere un perfil de usuario **avanzado** en el área privada de i-DE.

> **La serie 3.x está en fase alpha.** Es una reescritura de la integración 2.x y utiliza las estadísticas de Home Assistant en lugar de manipular directamente la base de datos del recorder. Lee las [notas de actualización](UPGRADE-TO-3.x.md) antes de migrar una instalación existente.

**Lee la [FAQ](FAQ.md) y las secciones Dependencias y Advertencias antes de instalar.**

## Funcionalidades de 3.x

- Integración con el panel de Energía de Home Assistant mediante estadísticas.
- Sensor de consumo acumulado basado en lecturas directas del contador.
- Estadísticas de consumo histórico con precisión sub-kWh.
- Estadísticas de generación histórica, desactivadas por defecto.
- Soporte para varios contratos/puntos de suministro mediante entradas de configuración independientes.
- Configuración desde la interfaz de Home Assistant, sin necesidad de YAML.
- Acceso asíncrono a la API e integración mediante `DataUpdateCoordinator`.
- Limitación de frecuencia persistente por dataset, de forma que los reinicios no reinician los intervalos normales de consulta.

### Intervalos de consulta actuales

El coordinador se despierta periódicamente, pero solo consulta a i-DE cuando el dataset correspondiente ha alcanzado su ventana de actualización:

| Dataset | Tras una consulta correcta | Tras un intento fallido |
| --- | ---: | ---: |
| Lectura directa / consumo acumulado | 6 horas | 5 minutos |
| Consumo histórico | 12 horas | 5 minutos |
| Generación histórica | 12 horas | 5 minutos |

Estos límites son intencionados. La API privada del punto de suministro de i-DE puede ser inestable y un exceso de solicitudes puede provocar bloqueos temporales de la cuenta.

### No disponible actualmente en 3.x

El código 3.x recibe un valor instantáneo junto con algunas lecturas directas del contador, pero **no expone actualmente una entidad separada de Consumo instantáneo**. La documentación antigua de 2.x que describía un sensor instantáneo o una actualización horaria entre los minutos 50 y 59 ya no corresponde con la implementación actual.

## Dependencias

Necesitas un usuario de i-DE con acceso al área privada. Puedes registrarte desde el [área de clientes de i-DE](https://www.i-de.es/consumidores/web/guest/login).

También necesitas el perfil de **Usuario avanzado**. Si tu cuenta no lo tiene, debes solicitarlo desde el perfil del área privada de i-DE.

La integración depende del cliente Python independiente [`ideenergy`](https://github.com/ldotlopez/ideenergy) y de [`homeassistant-historical-sensor`](https://github.com/ldotlopez/ha-historical-sensor).

## Instalación

### Repositorio personalizado de HACS

1. Abre HACS en Home Assistant.
2. Añade `https://github.com/ldotlopez/ha-ideenergy` como **Repositorio personalizado**, categoría **Integración**.
3. Descarga la versión deseada.
4. Reinicia Home Assistant.
5. Ve a **Ajustes → Dispositivos y servicios → Añadir integración** y selecciona **i-DE Energy Monitor**.
6. Introduce tus credenciales de i-DE y selecciona el contrato/punto de suministro que quieras monitorizar.

Para monitorizar varios puntos de suministro, crea una entrada de configuración independiente para cada contrato.

### Instalación manual

1. Descarga o clona este repositorio.
2. Copia `custom_components/ideenergy` dentro del directorio `custom_components` de tu configuración de Home Assistant.
3. Reinicia Home Assistant.
4. Añade **i-DE Energy Monitor** desde **Ajustes → Dispositivos y servicios**.
5. Introduce tus credenciales y selecciona el contrato que quieras monitorizar.

## Capturas

*Sensor de energía acumulada*

![snapshot](screenshots/accumulated.png)

*Sensor de histórico de energía*

![snapshot](screenshots/historical.png)

*Asistente de configuración*

![snapshot](screenshots/configuration-1.png)
![snapshot](screenshots/configuration-2.png)

## Advertencias

- La serie 3.x sigue siendo software alpha y puede cambiar entre versiones preliminares.
- i-DE no ofrece un contrato de API público para esta integración. Los cambios en su web o endpoints privados pueden romper la autenticación o la obtención de datos sin previo aviso.
- Las lecturas directas del contador son sensiblemente menos fiables que los datos históricos. No construyas automatizaciones críticas o de seguridad que dependan de ellas.
- Sé conservador con las lecturas directas cuando tengas varios contratos configurados. Un exceso de peticiones puede provocar bloqueos temporales por parte de i-DE.
- Los datos históricos llegan con retraso desde i-DE, normalmente de unas 24 a 48 horas.

## Licencia

Este proyecto se distribuye bajo la GNU General Public License v3.0. Consulta [LICENSE](LICENSE).

## Descargo de responsabilidad

ESTE PROYECTO NO ESTÁ ASOCIADO NI RELACIONADO DE NINGÚN MODO CON LAS EMPRESAS DEL GRUPO IBERDROLA NI CON NINGUNA OTRA. La información incluida aquí y en línea tiene fines educativos y de referencia; los desarrolladores no respaldan ni fomentan usos inapropiados y no asumen responsabilidad legal por la funcionalidad o seguridad de tus dispositivos.
