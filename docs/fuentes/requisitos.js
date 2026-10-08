// Genera docs/Requisitos_Kinemart.docx a partir de las tablas de este archivo.
// Uso (desde una carpeta con `npm i docx`):
//   node requisitos.js ../Requisitos_Kinemart.docx
// Despues, abrirlo en Word una vez para que se actualice el indice.

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  ShadingType, HeadingLevel, AlignmentType, BorderStyle, LevelFormat, Footer,
  PageNumber, TableOfContents, PageBreak,
} = require("docx");

const BOSQUE = "24493A", SALVIA = "A9B8AC", TINTA = "1D1A1B", TENUE = "5C6A62", FONDO_TABLA = "E8EFEA";
const ANCHO = 9360; // Carta con márgenes de 1"
const FUENTE = "Calibri";

const t = (text, o = {}) => new TextRun({ text, font: FUENTE, size: 21, color: TINTA, ...o });
const p = (contenido, o = {}) => new Paragraph({
  spacing: { after: 120, line: 288 }, ...o,
  children: (Array.isArray(contenido) ? contenido : [contenido]).map((c) => (typeof c === "string" ? t(c) : c)),
});
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text, font: FUENTE, size: 32, bold: true, color: BOSQUE })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text, font: FUENTE, size: 25, bold: true, color: BOSQUE })] });
const vineta = (contenido, nivel = 0) => new Paragraph({
  numbering: { reference: "vinetas", level: nivel }, spacing: { after: 60, line: 276 },
  children: (Array.isArray(contenido) ? contenido : [contenido]).map((c) => (typeof c === "string" ? t(c) : c)),
});
const b = (text) => t(text, { bold: true });

const borde = { style: BorderStyle.SINGLE, size: 4, color: "C9D3CC" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

function celda(texto, ancho, { cabecera = false, color, negrita = false } = {}) {
  return new TableCell({
    width: { size: ancho, type: WidthType.DXA }, borders: bordes,
    shading: cabecera ? { fill: BOSQUE, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    children: [new Paragraph({ children: [t(String(texto), {
      size: 19, bold: cabecera || negrita, color: cabecera ? "FFFFFF" : color || TINTA,
    })] })],
  });
}

const COLOR_ESTADO = { "Hecho": "1F7A4A", "Parcial": "8A5300", "Pendiente": "5C6A62", "Investigación": "5C6A62" };

function tabla(cabeceras, filas, anchos, { colEstado = -1 } = {}) {
  return new Table({
    width: { size: ANCHO, type: WidthType.DXA }, columnWidths: anchos,
    rows: [
      new TableRow({ tableHeader: true, children: cabeceras.map((c, i) => celda(c, anchos[i], { cabecera: true })) }),
      ...filas.map((f) => new TableRow({
        children: f.map((v, i) => celda(v, anchos[i], {
          color: i === colEstado ? COLOR_ESTADO[v] : undefined,
          negrita: i === 0 || i === colEstado,
        })),
      })),
    ],
  });
}
const espacio = () => new Paragraph({ spacing: { after: 80 }, children: [] });

// ---------------------------------------------------------------- Contenido
const RF = [
  ["Cuentas y acceso", [
    ["RF-01", "Registrar un negocio nuevo: crea la organización y su usuario propietario en un solo paso.", "Alta", "Hecho"],
    ["RF-02", "Iniciar sesión con correo y contraseña; la sesión se reanuda sola al volver a abrir el panel.", "Alta", "Hecho"],
    ["RF-03", "Roles por negocio (propietario, admin, vendedor, lectura) con permisos distintos en la API.", "Alta", "Hecho"],
    ["RF-04", "Invitar usuarios al negocio y asignarles un rol desde el panel.", "Alta", "Pendiente"],
    ["RF-05", "Recuperar la contraseña por correo.", "Media", "Pendiente"],
    ["RF-06", "Una persona puede pertenecer a varios negocios y elegir el negocio activo.", "Baja", "Parcial"],
    ["RF-07", "Verificación en dos pasos para el propietario.", "Baja", "Pendiente"],
  ]],
  ["Auditoría", [
    ["RF-08", "Registrar automáticamente quién creó, cambió o borró cada dato, con valor anterior y nuevo, fecha e IP.", "Alta", "Hecho"],
    ["RF-09", "Consultar la bitácora desde el panel, con filtros por usuario, fecha y tipo de dato.", "Media", "Pendiente"],
  ]],
  ["Catálogo", [
    ["RF-10", "Gestionar categorías y productos: SKU, código de barras, unidad, IVA y activo/inactivo.", "Alta", "Hecho"],
    ["RF-11", "Precio de venta con mínimo de negociación, y precio de compra con máximo.", "Alta", "Hecho"],
    ["RF-12", "Guardar el historial de cambios de precio de cada producto.", "Media", "Hecho"],
    ["RF-13", "Productos de tipo servicio, sin control de stock.", "Media", "Hecho"],
    ["RF-14", "Foto, descripción, precio de oferta y paquetes («3 por Bs 10») por producto.", "Media", "Pendiente"],
    ["RF-15", "Ofertas especiales (2x1, combo) con vigencia, que se aplican solas al vender.", "Baja", "Pendiente"],
    ["RF-16", "Variantes de producto (talla, color) con stock propio.", "Baja", "Pendiente"],
  ]],
  ["Terceros", [
    ["RF-17", "Clientes, proveedores y transportadoras (un mismo tercero puede ser varios), con contactos y ubicaciones.", "Alta", "Hecho"],
  ]],
  ["Ventas", [
    ["RF-18", "Punto de venta: buscar producto o código, armar líneas por unidad o por total directo.", "Alta", "Hecho"],
    ["RF-19", "Numeración correlativa de ventas y cotizaciones por negocio (V-0001, C-0001).", "Alta", "Hecho"],
    ["RF-20", "Estado de cobro (pagado, pendiente/fiado, parcial) y anulación de ventas.", "Alta", "Hecho"],
    ["RF-21", "Avisar y pedir confirmación al vender bajo el precio mínimo; la venta queda marcada.", "Alta", "Hecho"],
    ["RF-22", "Nota de venta pública por QR: el cliente la guarda en su galería, la manda por WhatsApp o la imprime en PDF.", "Alta", "Hecho"],
    ["RF-23", "Limitar a propietario y admin la autorización de ventas bajo el mínimo.", "Media", "Pendiente"],
    ["RF-24", "Registrar el método de pago (efectivo, QR, transferencia) y los pagos parciales de un fiado.", "Media", "Pendiente"],
  ]],
  ["Cotizaciones, listas y escaparate", [
    ["RF-25", "Cotizaciones con estado y conversión a venta en un clic.", "Alta", "Hecho"],
    ["RF-26", "Listas de compras o pendientes, sincronizadas con la PWA de listas.", "Media", "Hecho"],
    ["RF-27", "Catálogo público del negocio por enlace, sin costos, mínimos ni stock.", "Media", "Parcial"],
  ]],
  ["Inventario (Fase 4, pedido por el cliente el 30/07/2026)", [
    ["RF-28", "Registrar las sucursales o almacenes del negocio.", "Alta", "Pendiente"],
    ["RF-29", "Llevar el stock por producto, sucursal y lote.", "Alta", "Pendiente"],
    ["RF-30", "Lotes con fecha de llegada, fecha de vencimiento y proveedor.", "Alta", "Pendiente"],
    ["RF-31", "Todo cambio de stock genera un movimiento que no se edita (entrada, salida, ajuste, traspaso).", "Alta", "Pendiente"],
    ["RF-32", "Traspasar mercadería entre sucursales.", "Alta", "Pendiente"],
    ["RF-33", "Cada venta descuenta stock de la sucursal activa, empezando por el lote que vence primero.", "Alta", "Pendiente"],
    ["RF-34", "Alertas de stock bajo y de vencimiento próximo.", "Media", "Pendiente"],
    ["RF-35", "Conteo de inventario con lector de código de barras o con la cámara del celular.", "Alta", "Pendiente"],
    ["RF-36", "Historial de movimientos por producto y por sucursal.", "Media", "Pendiente"],
  ]],
  ["Compras", [
    ["RF-37", "Registrar compras a proveedores que ingresan stock por lote.", "Alta", "Pendiente"],
  ]],
  ["Reportes", [
    ["RF-38", "Reporte de ventas por día, sucursal, vendedor y producto.", "Media", "Pendiente"],
    ["RF-39", "Exportar notas y reportes en PDF A4 e imprimir ticket térmico de 80 mm.", "Media", "Pendiente"],
  ]],
  ["Plataforma", [
    ["RF-40", "Planes por negocio que habilitan funciones y límites (usuarios, sucursales, productos).", "Media", "Pendiente"],
    ["RF-41", "Avisos a sistemas externos (webhooks) por negocio: venta creada, stock bajo.", "Baja", "Pendiente"],
    ["RF-42", "Panel instalable como app (PWA) en iPhone y Android, con ícono de Kinemart.", "Alta", "Pendiente"],
    ["RF-43", "Tres modos visuales: noche, claro y tecno.", "Baja", "Hecho"],
    ["RF-44", "Cobro por QR Simple interoperable (BCB).", "Baja", "Investigación"],
  ]],
];

const RNF = [
  ["RNF-01", "Seguridad", "Ningún usuario ve datos de otro negocio.", "Filtro por organización en cada consulta (hecho) + RLS en PostgreSQL con prueba automática de aislamiento (pendiente)."],
  ["RNF-02", "Seguridad", "Toda comunicación va cifrada.", "HTTPS obligatorio; HTTP redirige; HSTS de 1 año."],
  ["RNF-03", "Seguridad", "Sesiones con vencimiento.", "Token de acceso de 60 min; refresco de 7 días con rotación."],
  ["RNF-04", "Seguridad", "Contraseñas robustas.", "Validación de largo, contraseñas comunes y solo números; nunca se guardan en texto plano."],
  ["RNF-05", "Privacidad", "Lo público no expone datos internos.", "La nota QR y el escaparate no muestran costos, mínimos ni stock; el enlace de la nota usa un UUID no adivinable."],
  ["RNF-06", "Auditoría", "Todo cambio queda registrado.", "Usuario, fecha, IP, valor anterior y nuevo por campo."],
  ["RNF-07", "Respaldo", "Respaldo diario recuperable.", "Copia cifrada (AES-256) cada noche, 30 días de retención; restauración probada el 07/10/2026."],
  ["RNF-08", "Disponibilidad", "El sistema está disponible en horario comercial.", "Objetivo 99%; la base no entra en pausa por inactividad."],
  ["RNF-09", "Rendimiento", "Respuestas rápidas desde Bolivia.", "< 1 s con la API activa (medido 0,5 s); < 2 s la primera petición tras inactividad (medido 1,85 s)."],
  ["RNF-10", "Usabilidad", "Pensado primero para el celular.", "Controles de al menos 44 px; el cobro siempre visible en el punto de venta."],
  ["RNF-11", "Compatibilidad", "Funciona en el iPhone del cliente.", "Safari de iOS 16.4 o superior; Chrome y Edge actuales; sin app nativa."],
  ["RNF-12", "Localización", "Adaptado a Bolivia.", "Español en tuteo, bolivianos (Bs), hora de La Paz, IVA 13% incluido en el precio."],
  ["RNF-13", "Mantenibilidad", "Cambios verificados antes de publicar.", "Pruebas automáticas en cada cambio (56 hoy); solo se despliega si pasan; entorno reproducible con Docker."],
  ["RNF-14", "Costo", "Operación barata hasta tener clientes que paguen.", "≤ US$5/mes de infraestructura; techo duro de US$10/mes."],
  ["RNF-15", "Trazabilidad", "Las notas QR impresas siguen funcionando.", "El dominio de las notas es definitivo antes de emitir notas reales."],
  ["RNF-16", "Accesibilidad", "Legible y usable con teclado.", "Contraste mínimo 4,5:1, foco visible, respeta «reducir movimiento»."],
  ["RNF-17", "Sin conexión", "El panel abre aunque se corte internet.", "La PWA muestra el último catálogo y avisa que no hay conexión (pendiente)."],
];

const RESTRICCIONES = [
  ["Equipo", "1 desarrollador (Mateo); proyecto propio, no de la universidad."],
  ["Costo de operación", "Plan Hobby de Railway compartido (US$5 incluidos, límite duro US$10) y Supabase gratuito (500 MB de base, 1 GB de archivos)."],
  ["Plataforma móvil", "El cliente usa iPhone y no hay Mac: no se puede compilar ni publicar una app nativa para iOS. Kinemart es una PWA."],
  ["Infraestructura", "API en Railway (US East, Virginia) y base en Supabase (us-east-1): no hay servidores en Sudamérica."],
  ["Dominio", "Pendiente el dominio de ArmonIA. El QR de cada nota queda atado al dominio con que se emitió."],
  ["Fiscal", "La nota de venta no es factura. La facturación electrónica del SIN queda fuera del alcance actual."],
  ["Conectividad", "Las tiendas pueden tener internet intermitente: el panel debe tolerar cortes."],
  ["Datos", "El repositorio es público: en demos y pruebas solo hay datos ficticios."],
];

const RIESGOS = [
  ["La base gratuita se pausa o se llena", "Alto", "Respaldo diario que la mantiene activa; pasar a Supabase Pro (US$25/mes) con el primer cliente que pague."],
  ["Railway apaga la API al llegar al límite de gasto", "Alto", "Aviso por correo en US$5; subir el límite antes de vender en serio."],
  ["Fuga de datos entre negocios", "Alto", "Filtro por organización en cada vista + RLS + prueba automática de aislamiento."],
  ["Notas emitidas con un dominio provisional", "Alto", "Fijar el dominio definitivo antes de la primera venta real."],
  ["No hay iPhone para probar", "Medio", "Emulación con el motor de Safari (WebKit) y pruebas con el cliente antes de cada entrega."],
  ["Crecimiento del alcance (inventario es grande)", "Alto", "Alcance por fases, acordado por escrito con el cliente."],
  ["Internet intermitente en la tienda", "Medio", "PWA con funcionamiento básico sin conexión (RF-42, RNF-17)."],
  ["Un solo desarrollador", "Medio", "Documentación al día, pruebas automáticas y despliegue reproducible."],
];

const FASES = [
  ["0–3", "Cimientos multi-tenant, seguridad y auditoría, catálogo y terceros, ventas, cotizaciones, nota QR, panel", "Hecho"],
  ["Infra", "Docker, CI, despliegue (Railway + Supabase + Cloudflare), respaldos", "Hecho"],
  ["Diseño", "Identidad Kinemart, modos noche/claro/tecno, versión celular", "Hecho"],
  ["Siguiente", "PWA instalable, invitar usuarios, planes por negocio, RLS", "Pendiente"],
  ["4", "Inventario por sucursal y lote, compras, código de barras", "Pendiente"],
  ["5", "Reportes y exportables (PDF A4, ticket 80 mm)", "Pendiente"],
  ["6", "Cobro por QR Simple (BCB)", "Investigación"],
  ["7", "Suscripciones; facturación SIN si un cliente la exige", "Pendiente"],
];

const FUERA = [
  "Facturación electrónica del SIN (la nota de venta no es factura).",
  "App nativa para iOS o Android (sin Mac; se cubre con la PWA).",
  "Contabilidad, planillas y nómina.",
  "Tienda en línea con pago dentro de la web.",
  "Varias monedas (hoy todo es en Bs).",
];

const PREGUNTAS = [
  "¿Cómo se llaman las dos sucursales y cuál es la principal?",
  "¿Cuántas personas usarían el sistema y con qué rol (dueño, encargado, vendedor)?",
  "¿El control por lote y vencimiento es para todos los productos o solo para algunos (por ejemplo, alimentos)?",
  "¿Qué lector de código de barras tiene o piensa comprar? ¿Los productos traen el código del fabricante o pone códigos propios?",
  "¿Cómo hace hoy los traspasos entre sucursales y quién los autoriza?",
  "¿Necesita emitir factura del SIN o le basta la nota de venta?",
  "¿Imprime notas? ¿Con qué impresora (térmica de 80 mm, carta)?",
  "¿Qué métodos de pago recibe (efectivo, QR bancario, transferencia)?",
  "¿Qué datos revisa hoy cuando está de viaje y cada cuánto?",
];

const HU = [
  ["HU-01", "Registrar mi negocio", "propietario", "registrar mi negocio con mi correo", "empezar a vender el mismo día sin instalar nada", ["Con nombre del negocio, mi nombre, correo y contraseña se crean el negocio y mi usuario.", "Quedo dentro del panel como propietario."], "RF-01", "Hecho"],
  ["HU-02", "Entrar y seguir donde estaba", "vendedor", "entrar con mi correo y que el panel recuerde mi sesión", "no escribir la contraseña cada vez que abro el celular", ["Si la contraseña es incorrecta, el mensaje lo dice sin revelar si el correo existe.", "Al volver a abrir el panel dentro de 7 días, entro sin escribir la contraseña."], "RF-02", "Hecho"],
  ["HU-03", "Invitar a mi vendedor", "propietario", "invitar a un vendedor con su correo y elegir su rol", "que venda sin darle acceso a costos ni a borrar datos", ["El invitado recibe un enlace para crear su contraseña.", "Un vendedor no puede editar el catálogo ni borrar documentos."], "RF-03, RF-04", "Pendiente"],
  ["HU-04", "Recuperar mi contraseña", "usuario", "recibir un enlace para crear una contraseña nueva", "no quedar fuera de mi tienda", ["El enlace vence en 1 hora y sirve una sola vez."], "RF-05", "Pendiente"],
  ["HU-05", "Saber quién cambió un precio", "propietario", "ver quién cambió un precio, cuándo y de cuánto a cuánto", "detectar errores o abusos", ["Veo el historial de precios del producto.", "Puedo filtrar la bitácora por usuario y fecha desde el panel."], "RF-08, RF-09, RF-12", "Parcial"],
  ["HU-06", "Cargar un producto", "propietario", "cargar un producto con su código de barras, precio y precio mínimo", "venderlo escaneándolo y sin que lo regalen", ["El SKU y el código de barras no se repiten dentro del negocio.", "El mínimo no puede ser mayor que el precio de venta."], "RF-10, RF-11", "Hecho"],
  ["HU-07", "Mostrar fotos y ofertas", "propietario", "agregar foto, descripción y precio de oferta a un producto", "que el catálogo que comparto se vea atractivo", ["La foto se reduce en el celular antes de subir.", "El precio normal aparece tachado junto al de oferta."], "RF-14, RF-27", "Pendiente"],
  ["HU-08", "Vender rápido en el mostrador", "vendedor", "buscar o escanear un producto y cobrar en pocos toques", "no hacer esperar al cliente", ["Enter agrega lo buscado; repetir un producto suma una unidad.", "En el celular, el total y «Cobrar» quedan siempre a la vista."], "RF-18, RF-19", "Hecho"],
  ["HU-09", "Vender bajo el mínimo con permiso", "vendedor", "que el sistema me avise si un precio queda bajo el mínimo", "no regalar mercadería por error", ["Antes de cobrar se pide confirmación.", "La venta queda marcada y se puede filtrar.", "Solo propietario o admin pueden autorizarla (pendiente)."], "RF-21, RF-23", "Parcial"],
  ["HU-10", "Darle su nota al cliente", "cliente final", "escanear un QR y guardar mi nota de venta", "tener el comprobante en mi celular", ["La nota abre sin cuenta.", "Puedo guardarla como imagen, mandarla por WhatsApp o imprimirla en PDF.", "La nota no muestra costos ni stock."], "RF-22", "Hecho"],
  ["HU-11", "Fiar y cobrar después", "vendedor", "marcar una venta como fiada y registrar luego los pagos", "saber cuánto me debe cada cliente", ["La venta fiada aparece como pendiente.", "Cada pago registra monto, método y fecha (pendiente)."], "RF-20, RF-24", "Parcial"],
  ["HU-12", "Cotizar y convertir en venta", "vendedor", "enviar una cotización y convertirla en venta si el cliente acepta", "no volver a cargar los productos", ["La venta copia las líneas y la cotización queda aceptada."], "RF-25", "Hecho"],
  ["HU-13", "Registrar mis sucursales", "propietario", "registrar mis dos sucursales", "llevar el stock de cada una por separado", ["Cada venta y movimiento pertenece a una sucursal.", "El panel muestra la sucursal activa."], "RF-28", "Pendiente"],
  ["HU-14", "Recibir mercadería por lote", "encargado", "registrar una compra con su lote, fecha de llegada y vencimiento", "saber qué vence primero y de qué proveedor vino", ["La compra suma stock en la sucursal que la recibe.", "Cada lote guarda proveedor, llegada y vencimiento."], "RF-30, RF-37", "Pendiente"],
  ["HU-15", "Ver el stock de cada sucursal", "propietario", "ver el stock de un producto en cada sucursal y por lote", "decidir qué reponer o traspasar", ["La vista muestra cantidades por sucursal y el lote más próximo a vencer."], "RF-29", "Pendiente"],
  ["HU-16", "Traspasar entre sucursales", "encargado", "mandar mercadería de una sucursal a otra", "no quedarme sin stock en una mientras sobra en la otra", ["El traspaso descuenta de la sucursal origen y suma en la destino.", "Queda registrado quién lo hizo y cuándo."], "RF-31, RF-32", "Pendiente"],
  ["HU-17", "Enterarme a tiempo", "propietario", "recibir alertas de stock bajo y de productos por vencer", "reponer o rematar antes de perder plata", ["Puedo fijar el stock mínimo por producto.", "Veo los lotes que vencen en los próximos 15 días."], "RF-34", "Pendiente"],
  ["HU-18", "Contar el inventario escaneando", "encargado", "contar el inventario con el lector o con la cámara del celular", "terminar el conteo en menos tiempo y sin errores", ["Cada escaneo suma uno al producto.", "Al cerrar el conteo, las diferencias generan ajustes registrados."], "RF-35", "Pendiente"],
  ["HU-19", "Que la venta descuente stock", "propietario", "que cada venta descuente el stock de la sucursal donde se hizo", "tener el inventario al día sin hacer nada extra", ["Se descuenta primero del lote que vence antes.", "Si no hay stock suficiente, el sistema avisa."], "RF-31, RF-33", "Pendiente"],
  ["HU-20", "Revisar las ventas del día", "propietario", "ver cuánto vendí hoy por sucursal y vendedor", "controlar el negocio aunque no esté presente", ["El reporte muestra totales por sucursal, vendedor y producto.", "Se puede exportar en PDF."], "RF-38, RF-39", "Pendiente"],
  ["HU-21", "Imprimir el ticket", "vendedor", "imprimir la nota en una impresora térmica de 80 mm", "entregar un comprobante en papel a quien lo pida", ["El ticket incluye el QR de la nota."], "RF-39", "Pendiente"],
  ["HU-22", "Instalar Kinemart en el celular", "propietario", "instalar el panel en la pantalla de inicio de mi iPhone", "abrirlo como una app, con su ícono", ["Safari ofrece «Agregar a pantalla de inicio» con el ícono de la K.", "Abre a pantalla completa, sin la barra del navegador."], "RF-42", "Pendiente"],
  ["HU-23", "Controlar todo desde el viaje", "propietario de viaje", "ver ventas y stock de mis dos sucursales desde el celular", "no depender de que me llamen para saber cómo va el negocio", ["Veo el resumen del día de cada sucursal.", "Funciona con conexión lenta."], "RF-29, RF-38, RF-42", "Pendiente"],
  ["HU-24", "Compartir mi catálogo", "propietario", "compartir por WhatsApp un enlace a mi catálogo", "que mis clientes vean qué tengo sin escribirme", ["El enlace abre una página pública con productos y precios, sin costos ni stock."], "RF-27", "Parcial"],
];

const TODOS = RF.flatMap(([, f]) => f);
const TOTAL_RF = TODOS.length;
const HECHOS = TODOS.filter((f) => f[3] === "Hecho").length;
const PARCIALES = TODOS.filter((f) => f[3] === "Parcial").length;

// ---------------------------------------------------------------- Documento
const cuerpo = [];
cuerpo.push(
  new Paragraph({ spacing: { before: 1800, after: 120 }, children: [t("Especificación de requisitos", { size: 52, bold: true, color: BOSQUE })] }),
  new Paragraph({ spacing: { after: 360 }, children: [t("Kinemart — ERP para comercios", { size: 32, color: TINTA })] }),
  p([b("Versión: "), t("0.1 · Borrador para revisión")]),
  p([b("Fecha: "), t("8 de octubre de 2026")]),
  p([b("Autor: "), t("Luis Mateo Hurtado Castro — Kinemart by ArmonIA")]),
  p([b("Objetivo del documento: "), t("fijar qué debe hacer el sistema (requisitos funcionales), con qué calidad (no funcionales) y bajo qué límites, para derivar las historias de usuario y planificar las próximas fases.")]),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ spacing: { after: 200 }, children: [t("Contenido", { size: 28, bold: true, color: BOSQUE })] }),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
);

cuerpo.push(
  h1("1. Resumen"),
  p("Kinemart es un ERP en la nube para comercios pequeños de Bolivia: punto de venta, cotizaciones, catálogo, clientes y, en la siguiente fase, inventario por sucursal y lote. Cada negocio tiene sus datos aislados de los demás (multi-tenant)."),
  p(`Hoy está desplegado y funcionando: la API en Railway, la base en Supabase y el panel en Cloudflare. De los ${TOTAL_RF} requisitos funcionales, ${HECHOS} están hechos y ${PARCIALES} a medias; lo que más pesa en lo pendiente es el inventario que pidió el primer cliente.`),
  p([b("Para revisar: "), t("la sección 9 (preguntas para el cliente) define el diseño del inventario. La sección 10 traduce los requisitos a historias de usuario.")]),

  h1("2. Contexto y objetivos"),
  h2("2.1 Situación del primer cliente"),
  vineta("Comercio con 2 sucursales; el dueño hace viajes departamentales y se ausenta seguido."),
  vineta("El inventario lo lleva a mano y cada vez le toma más tiempo."),
  vineta("Usa solo iPhone."),
  vineta("El 30/07/2026 pidió explícitamente inventario con lotes, vencimientos, proveedores y código de barras."),
  h2("2.2 Prioridades del cliente (en orden)"),
  vineta("Vender rápido y entregar una nota con QR al cliente."),
  vineta("Saber el stock real de cada sucursal, por lote y con fecha de vencimiento."),
  vineta("Contar inventario con lector de código de barras."),
  vineta("Controlar el negocio desde el celular mientras está de viaje."),
  h2("2.3 Objetivos del producto"),
  vineta("Un solo sistema para varios negocios (SaaS), cada uno con sus datos aislados."),
  vineta("Que funcione bien en el celular, sin instalar nada desde una tienda de apps."),
  vineta("Costo de operación mínimo hasta tener clientes que paguen."),

  h1("3. Actores y roles"),
  tabla(["Actor", "Qué hace", "Acceso"], [
    ["Propietario", "Dueño del negocio. Configura el catálogo, ve todo, autoriza excepciones.", "Panel, todo el negocio"],
    ["Admin", "Encargado de confianza. Mismos permisos que el propietario en el día a día.", "Panel, todo el negocio"],
    ["Vendedor", "Vende, cotiza y gestiona clientes y listas. No edita el catálogo ni borra.", "Panel, operación"],
    ["Lectura", "Consulta sin modificar (contador, socio).", "Panel, solo lectura"],
    ["Cliente final", "Recibe la nota de venta por QR y mira el catálogo público.", "Enlaces públicos, sin cuenta"],
    ["Plataforma", "Administra Kinemart: negocios, planes y soporte.", "Admin de Django"],
  ], [1700, 5160, 2500]),
);

cuerpo.push(h1("4. Requisitos funcionales"));
cuerpo.push(p("Estado al 8 de octubre de 2026. Prioridad según el pedido del cliente y lo que destraba al resto."));
for (const [modulo, filas] of RF) {
  cuerpo.push(h2(modulo));
  cuerpo.push(tabla(["ID", "Requisito", "Prioridad", "Estado"], filas, [900, 6060, 1100, 1300], { colEstado: 3 }));
  cuerpo.push(espacio());
}

cuerpo.push(
  h1("5. Requisitos no funcionales"),
  tabla(["ID", "Categoría", "Requisito", "Criterio de aceptación"], RNF, [950, 1450, 2700, 4260]),
  h1("6. Restricciones"),
  tabla(["Restricción", "Detalle"], RESTRICCIONES, [2200, 7160]),
  h1("7. Riesgos y mitigación"),
  tabla(["Riesgo", "Impacto", "Mitigación"], RIESGOS, [3200, 1000, 5160]),
  h1("8. Alcance por fases"),
  tabla(["Fase", "Contenido", "Estado"], FASES, [1300, 6560, 1500], { colEstado: 2 }),
  h2("Fuera del alcance actual"),
  ...FUERA.map((f) => vineta(f)),
  h1("9. Preguntas pendientes para el cliente"),
  p("Las respuestas definen el modelo de inventario de la Fase 4."),
  ...PREGUNTAS.map((q) => vineta(q)),
  h1("10. Historias de usuario"),
  p("Formato: como <rol>, quiero <acción>, para <beneficio>. Cada historia indica los requisitos que cubre y su estado."),
);

for (const [id, titulo, rol, accion, para, criterios, rfs, estado] of HU) {
  cuerpo.push(
    new Paragraph({ keepNext: true, spacing: { before: 220, after: 60 }, children: [
      t(`${id} · ${titulo}`, { bold: true, size: 22, color: BOSQUE }),
      t(`   ${estado}`, { bold: true, size: 19, color: COLOR_ESTADO[estado] }),
    ] }),
    new Paragraph({ keepNext: true, spacing: { after: 60, line: 276 }, children: [
      t("Como "), b(rol), t(", quiero "), t(accion), t(", para "), t(para), t("."),
    ] }),
    ...criterios.map((c) => vineta(c)),
    new Paragraph({ spacing: { after: 80 }, children: [t(`Cubre: ${rfs}`, { size: 18, color: TENUE })] }),
  );
}

const doc = new Document({
  creator: "Luis Mateo Hurtado Castro",
  title: "Especificación de requisitos — Kinemart",
  styles: { default: { document: { run: { font: FUENTE, size: 21 } } } },
  numbering: { config: [{ reference: "vinetas", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
    { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } },
  ] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      t("Kinemart · Especificación de requisitos · ", { size: 16, color: TENUE }),
      new TextRun({ children: [PageNumber.CURRENT], font: FUENTE, size: 16, color: TENUE }),
    ] })] }) },
    children: cuerpo,
  }],
});

const destino = process.argv[2];
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(destino, buf); console.log("escrito", destino, buf.length, "bytes"); });
