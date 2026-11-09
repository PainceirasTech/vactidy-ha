# Vactidy para Home Assistant

Integración local para robots aspiradores **Vactidy** (e modelos compatibles baseados en
Tuya) que falan o protocolo LAN de Tuya 3.3. Sen nube, sen conta, sen dependencias do
fabricante: Home Assistant fala co robot directamente por TCP no porto 6668.

[Español](README.md) · [English](README.en.md)

> **Estado:** v0.1.0. Probado nun **Vactidy Cleanova W15** (`productId`
> `ut96oplbcckfxwwu`, firmware `40.00`, protocolo `2.2`), cuxo mapa de data points
> coincide case por completo co Proscenic M9.

---

## Que achega

- Entidade `vacuum` completa: iniciar, pausar, deter, volver á base, localizar e cambiar
  a potencia de succión.
- 12 sensores: batería, superficie e tempo da limpeza actual, acumulados, vida útil de
  cepillos, sensores e mopa, e código de avería traducido.
- 5 sensores binarios: cargando, na base, problema, non molestar e mopa instalada.
- 2 selectores: caudal de auga da mopa e modo de limpeza (barrer / fregar / ambas).
- 2 interruptores: modo non molestar e luz do panel.
- 6 botóns: localizar, baleirar depósito e reiniciar os catro contadores de mantemento.
- Diagnóstico descargable desde a propia entrada, sen expoñer a clave local.

## Requisitos

- Home Assistant 2024.11 ou superior.
- O robot e Home Assistant na mesma rede local.
- A **clave local** do dispositivo: 16 caracteres que o fabricante entrega ao vincular o
  robot e que non caduca. Pódese obter de dúas formas:
  1. Con `tinytuya wizard`, que a descarga da API de Tuya Cloud pedindo as claves da túa
     conta de desenvolvedor.
  2. Extraéndoa do propio teléfono se xa tes a app Tuya vinculada
     (`shared_prefs/spUtils.xml`, campo `localKey`).
- Unha **IP fixa** para o robot. Recoméndase reservala no router por MAC.

## Instalación

### HACS (recomendado)

1. HACS → Integracións → menú de tres puntos → **Repositorios personalizados**.
2. Engade `https://github.com/PainceirasTech/vactidy-ha` coa categoría **Integration**.
3. Busca **Vactidy**, instala e reinicia Home Assistant.

### Manual

Copia a carpeta `custom_components/vactidy` dentro de `config/custom_components/` da túa
instalación de Home Assistant e reinicia.

## Configuración

1. Axustes → Dispositivos e servizos → **Engadir integración** → *Vactidy*.
2. Enche os catro campos:

| Campo | Exemplo | De onde se obtén |
| --- | --- | --- |
| Enderezo IP | `192.168.5.210` | Reserva DHCP do router |
| ID do dispositivo | `bf3e20ee26fbdcffd8e8kl` | `tinytuya wizard` ou a app |
| Clave local | 16 caracteres | `tinytuya wizard` ou `spUtils.xml` |
| Nome | `Robot salón` | O que queiras |

A integración valida a conexión antes de gardar: se a clave é incorrecta verás **«A clave
local foi rexeitada»**, e se a IP non responde, **«Non se pode acadar o robot»**. Se máis
adiante cambia a IP ou rotas a clave, usa **Reconfigurar** na entrada; non fai falta
borrala.

## Entidades

| Plataforma | Entidades |
| --- | --- |
| `vacuum` | Robot (estado, batería, potencia, iniciar / pausar / deter / base / localizar) |
| `sensor` | Batería, superficie limpiada, tempo de limpeza, estado, superficie total, limpezas totais, tempo total, vida do cepillo lateral, cepillo principal, sensores, mopa, avería |
| `binary_sensor` | Cargando, na base, problema, non molestar, mopa instalada |
| `select` | Caudal de auga, modo de limpeza |
| `switch` | Non molestar, luz do panel |
| `button` | Localizar, baleirar depósito, reiniciar cepillo lateral, principal, sensores e mopa |

A entidade `vacuum` expón ademais como atributos o estado en cru, a superficie e o tempo
da limpeza, o modo, o caudal, se a mopa está posta, o número de limpezas e o código de
avería coa súa descrición.

## Como funciona

O cliente (`tuya_local.py`) implementa o protocolo local de Tuya 3.3 en asyncio puro:

- Tramas `55AA`: cabeceira de 16 bytes, corpo cifrado e pé con CRC32 + sufixo.
- Cifrado **AES-128-ECB** coa clave local tal cal, sen hash.
- Consulta con `DP_QUERY (0x0A)` e escritura con `CONTROL (0x07)`.
- O robot responde repetindo o comando recibido, non con `STATUS (0x08)`; o cliente
  acepta calquera mensaxe que traia `dps`.

Non se usa a nube en ningún momento. O único requisito externo é `cryptography`, que xa
vén con Home Assistant.

## Limitacións e folla de ruta

- **Mapas e limpeza por zonas**: os data points `14` (traza) e `16` (petición de mapa)
  están identificados pero o seu formato binario non está documentado; aínda non se
  implementan.
- **Control manual por dirección** (`12`): non exposto, para non competir coa app.
- **Frecuencia de baleirado** (`37`) e **volume** (`26`): pendentes de expoñer.
- A integración sondea cada 30 s; o estado refréscase ao instante tras cada comando.

## Capturas

| Ficheiro | Contido |
| --- | --- |
| `docs/images/integracion.png` | A integración engadida en Axustes → Dispositivos e servizos |
| `docs/images/tarjeta.png` | Tarxeta do robot coas súas entidades no panel |
| `docs/images/configuracion.png` | Formulario de alta cos catro campos |

## Licenza

MIT. Consulta [LICENSE](LICENSE).

## Aviso

Proxecto non oficial, sen relación con Vactidy nin con Tuya. Usa o protocolo local por
enxeñería inversa do tráfico do teu propio dispositivo. Se actualizas o firmware do
robot, o mapa de data points podería cambiar.
