# Vactidy para Home Assistant

Integración local para robots aspiradores **Vactidy** (e modelos compatibles baseados en
Tuya) que falan o protocolo LAN de Tuya 3.3. Sen nube, sen conta e sen depender do
fabricante: Home Assistant fala co robot directamente pola túa rede wifi.

[Español](README.md) · [English](README.en.md)

> **Estado:** v0.1.4. Probado nun **Vactidy Cleanova W15** (`productId`
> `ut96oplbcckfxwwu`, firmware `40.00`, protocolo `2.2`), cuxo mapa de data points
> coincide case por completo co Proscenic M9.

---

## Que vas conseguir

Un robot integrado en Home Assistant con:

- **Entidade `vacuum`**: iniciar, pausar, deter, volver á base, localizar e cambiar a
  potencia de succión.
- **12 sensores**: batería, superficie e tempo da limpeza, acumulados, vida útil dos
  cepillos, sensores e mopa, e o código de avaría traducido.
- **5 sensores binarios**: cargando, na base, problema, non molestar e mopa instalada.
- **2 selectores**: caudal de auga da mopa e modo de limpeza (barrer / fregar / ambas).
- **2 interruptores**: modo non molestar e luz do panel.
- **6 botóns**: localizar, baleirar o depósito e reiniciar os contadores de mantemento.

Todo funciona en local: se cae internet, o robot segue respondendo.

## Antes de comezar

Necesitas catro cousas:

1. Home Assistant **2024.11 ou superior**.
2. Acceso ao **Marketplace** de integracións. Se tes Home Assistant **2026.11 ou
   posterior**, o Marketplace vén incluído: está en *Axustes → Marketplace*. En versións
   anteriores chámase **HACS** e hai que instalalo (paso 1).
3. O robot **acendido e na mesma rede** que Home Assistant.
4. Dez minutos e a **clave local** do robot. Se non a tes, o paso 5 explica como
   conseguila sen usar a terminal.

---

## Paso 1 · Abrir o Marketplace

**Home Assistant 2026.11 ou posterior:** o Marketplace xa vén dentro de Home Assistant.
Entra en *Axustes → Marketplace* e salta ao paso 2. Non hai que instalar nada.

**Versións anteriores:** o mesmo catálogo chámase **HACS** e instálase á parte.

1. Instala o complemento **Terminal & SSH** desde *Axustes → Complementos → Tenda de
   complementos*, ou entra por SSH na túa instalación.
2. Executa:

   ```bash
   wget -O - https://get.hacs.xyz | bash -
   ```

3. Reinicia Home Assistant.
4. Vai a *Axustes → Dispositivos e servizos → Engadir integración* e busca **HACS**.
   Acéptao todo e, cando che pida autorizar en GitHub, introduce o código que che mostra.

## Paso 2 · Instalar Vactidy

**Se Vactidy xa aparece no catálogo** (búscao en *Marketplace → Integracións*), abre a
ficha e pulsa **Descargar**. Salta ao paso 3.

**Se aínda non aparece**, a inclusión no catálogo segue en revisión e hai que engadir o
repositorio á man:

1. Abre **Marketplace** (ou **HACS**) na barra lateral.
2. Entra en **Integracións**.
3. Arriba á dereita, menú de tres puntos → **Repositorios personalizados**
   (*Custom repositories*).
4. Pega o enderezo e escolle a categoría:

   | Campo | Valor |
   | --- | --- |
   | Repositorio | `https://github.com/PainceirasTech/vactidy-ha` |
   | Categoría | **Integration** |

5. Pulsa **Engadir**, busca **Vactidy**, abre a ficha e pulsa **Descargar**.

## Paso 3 · Reiniciar Home Assistant

Reinicia desde *Axustes → Sistema → Reiniciar*.

O reinicio non é opcional: ata que non reinicies, Home Assistant non ve a integración.

## Paso 4 · Engadir a integración

1. Vai a *Axustes → Dispositivos e servizos*.
2. Pulsa **Engadir integración** (abaixo á dereita).
3. Busca **Vactidy** e ábreo.
4. Aparece un menú con dúas opcións:

   ```
   Como queres configurar o robot?
     ▸ Xa teño a clave local
     ▸ Obtela de Tuya Cloud
   ```

   Escolle a que corresponda ao teu caso. A segunda é a fácil se nunca oíches falar dunha
   «clave local».

A integración busca o robot na túa rede mentres amosas ese menú. Se o atopa, verás a súa IP
e o seu identificador no texto de arriba; se non, non pasa nada, escríbense a man.

## Paso 5 · Conseguir a clave local

A **clave local** é un texto de 16 caracteres co que o robot cifra a comunicación.
Asínaa o fabricante e non cambia nunca. Sen ela non hai forma de falar co robot: é a
única peza que non se pode adiviñar.

Hai tres camiños. Escolle o que che encaixe.

### Camiño 1 · Xa a tes

Se alguén cho deu (por exemplo, quen che instalou a integración), salta ao paso 6.

### Camiño 2 · Mover o robot a Tuya Smart ou Smart Life

Este robot é Tuya por dentro aínda que a súa app se chame Vactidy. As apps de marca branca
**non deixan vincular a conta a un proxecto de Tuya**: o único código QR que ofrecen é
para engadir membros ao fogar. As apps oficiais de Tuya si o permiten.

1. Instala **Tuya Smart** ou **Smart Life** e crea unha conta na túa mesma rexión.
2. Na app de Vactidy, elimina o robot (*axustes do robot → quitar dispositivo*). Un
   dispositivo Tuya só pode estar nunha conta á vez.
3. Engade o robot en Tuya Smart igual que a primeira vez (Wi-Fi de 2,4 GHz). A
   configuración que garda o robot, mapas incluídos, vive no propio robot e non na app,
   así que o normal é que siga aí.
4. Segue a **Opción A** de aquí abaixo para pedir a clave desde Home Assistant.

Se prefires non tocar a app, vai ao camiño 3.

### Camiño 3 · Extraela do móbil, sen cambiar de app

A app garda a clave nun ficheiro interno. Só se pode ler con acceso ao almacenamento da
aplicación: un Android con root ou unha copia de seguridade completa.

1. Nun Android con root, abre `shared_prefs/spUtils.xml` dentro de
   `/data/data/<paquete da app>/`.
2. Dentro hai un JSON con `"localKey":"..."`. Eses 16 caracteres son a clave.

Non funciona en iPhone nin en Android sen root. Se non podes, o camiño 2 é a
alternativa.

### Opción A · Pedirlla a Tuya (solo con Tuya Smart ou Smart Life)

Só fai falta unha conta gratuíta de desenvolvedor e vincular a app do móbil.

1. Entra en <https://iot.tuya.com> e crea unha conta (é gratis; non fai falta tarxeta).
2. No menú lateral, **Cloud → Project Management**, e pulsa **Create Cloud Project**.
   - *Industry*: Smart Home.
   - *Development Method*: Smart Home.
   - *Data Center*: **Central Europe** se estás en España.
3. Abre o proxecto e apunta o **Access ID** e o **Access Secret** da pestana *Overview*.
4. No menú do proxecto, **Devices → Link Tuya App account → Add App Account**. Este paso
   faise na web, non na app: aparece un código QR.
5. No móbil, abre **Tuya Smart** ou **Smart Life** → pestana *Eu* → icona de escaneo →
   escanea o QR → confirma.
6. Volve a **Devices**: o robot aparece na lista. Xa está vinculado.

Agora, en Home Assistant:

1. Escolle **Obtela de Tuya Cloud** no menú da integración.
2. Enche Access ID, Access Secret e a rexión, e pulsa enviar.
3. Se o robot aparece, énchese só. Se non, escribe o seu identificador á man.

## Paso 6 · Rematar e comprobar

1. No formulario final, escolle o **nome** do robot. É opcional: se o deixas baleiro
   chamarase *Robot aspirador*.
2. Pulsa **Enviar**. A integración abre unha conexión de proba:
   - Se o robot responde, a entrada queda creada e as entidades aparecen soas.
   - Se algo falla, verás o erro explicado no apartado seguinte.
3. Comproba en *Axustes → Dispositivos e servizos → Vactidy* que o estado é **Na base**
   ou **Cargando**, coa batería ao nivel real.

Proba rápida: abre a tarxeta do robot e pulsa **Localizar**. O robot debería dicir algo.
Despois, **Volver á base** devólveo ao seu sitio.

## Se algo vai mal

| O que ves | Que significa | Que facer |
| --- | --- | --- |
| «Non se pode alcanzar o robot» | A IP non responde no porto 6668 | Comproba que o robot está acendido e na mesma rede; revisa que a IP non cambiase (ponlle IP fixa no router) |
| «A clave local foi rexeitada» | A clave ten 16 caracteres pero non é a do robot | Vólvea copiar completa, sen espazos; se a rexeneraches na app, usa a nova |
| «O dispositivo respondeu, pero non informa os puntos de datos esperados» | É un aparello Tuya, pero non desta familia | Este modelo non é compatible; abre unha incidencia co modelo exacto |
| Non aparece Vactidy ao engadir a integración | Non se reiniciou tras instalar | Reinicia Home Assistant e volve a *Axustes → Dispositivos e servizos* |
| A integración non atopa o robot | Difusión bloqueada ou o robot está noutra subrede | Escribe a IP e o identificador a man; están na app Tuya, en *Axustes do dispositivo → Información do dispositivo* |
| «Autenticación de Tuya Cloud rexeitada» | Access ID ou Secret incorrectos | Cóppiaos outra vez de *Overview*; ollo, non son os da app senón os do proxecto |
| «A conta de Tuya non ten dispositivos vinculados» | Falta o paso do QR | Repite *Devices → Link Tuya App account* |

O rexistro completo está en *Axustes → Sistema → Rexistros*, filtrando por `vactidy`.

## Entidades que aparecen

| Plataforma | Entidades |
| --- | --- |
| `vacuum` | Robot (estado, batería, potencia, iniciar / pausar / deter / base / localizar) |
| `sensor` | Batería, superficie limpada, tempo de limpeza, estado, superficie total, limpezas totais, tempo total, vida de cepillo lateral, cepillo principal, sensores, mopa, avaría |
| `binary_sensor` | Cargando, na base, problema, non molestar, mopa instalada |
| `select` | Caudal de auga, modo de limpeza |
| `switch` | Non molestar, luz do panel |
| `button` | Localizar, baleirar depósito, reiniciar cepillo lateral, principal, sensores e mopa |

A entidade `vacuum` expón ademais como atributos o estado en cru, a superficie e o tempo da
limpeza, o modo, o caudal, se a mopa está posta, o número de limpezas e o código de avaría
coa súa descrición.

## Compatibilidade

O mapa de data points que usa esta integración **non é de Vactidy**: é o que Tuya comparte
entre varias marcas brancas. O W15 coincide case ao 100 % co Proscenic M9, e por iso é moi
probable que funcione noutros robots co mesmo `productId` ou similar.

Se o teu robot usa outro mapa, a integración detéctao ao configurala e diche con o erro
«non informa os puntos de datos esperados» en vez de crear entidades rotas.

Modelos confirmados:

| Modelo | Estado |
| --- | --- |
| Vactidy Cleanova W15 | Probado |
| Outros Vactidy con Tuya 3.3 | Sen probar; proba e cóntao nunha incidencia |

## Como funciona (para curiosos)

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
  están identificados pero o seu formato binario non está documentado; non se implementan
  aínda.
- **Control manual por dirección** (`12`): non exposto, para non competir coa app.
- **Frecuencia de baleirado** (`37`) e **volume** (`26`): pendentes de expoñer.
- A integración sonda cada 30 s; o estado actualízase ao instante tras cada comando.

## Capturas

As imaxes viven en `docs/images/`:

| Ficheiro | Contido |
| --- | --- |
| `docs/images/integracion.png` | A integración engadida en Axustes → Dispositivos e servizos |
| `docs/images/tarjeta.png` | Tarxeta do robot coas súas entidades no panel |
| `docs/images/configuracion.png` | Formulario de alta co robot xa detectado e a clave local como único campo manual |

## Licenza

MIT. Consulta [LICENSE](LICENSE).

## Aviso

Proxecto non oficial, sen relación con Vactidy nin con Tuya. Usa o protocolo local por
enxeñería inversa do tráfico do teu propio dispositivo. Se actualizas o firmware do robot,
o mapa de data points podería cambiar.
