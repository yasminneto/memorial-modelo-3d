import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
let artifactEntry;
try {
  artifactEntry = require.resolve("@oai/artifact-tool");
} catch {
  const runtimeModules = process.env.RUNTIME_NODE_MODULES;
  if (!runtimeModules) {
    throw new Error("@oai/artifact-tool not found. Set RUNTIME_NODE_MODULES to the bundled Node modules directory.");
  }
  artifactEntry = require.resolve("@oai/artifact-tool", { paths: [runtimeModules] });
}
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

function parseArgs(argv) {
  const values = {};
  for (let index = 2; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error("Usage: build_memorial.mjs --spec memorial_spec.json --output memorial.pptx [--qa-dir folder]");
    }
    values[key.slice(2)] = value;
  }
  if (!values.spec || !values.output) throw new Error("--spec and --output are required");
  return values;
}

async function imageBytes(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function contentType(imagePath) {
  const extension = path.extname(imagePath).toLowerCase();
  if (extension === ".jpg" || extension === ".jpeg") return "image/jpeg";
  if (extension === ".webp") return "image/webp";
  return "image/png";
}

function addText(slide, name, text, position, style) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = style;
  return shape;
}

function sourceLabel(value) {
  const labels = { model: "modelo", briefing: "briefing", reference: "referência", user: "usuário", pending: "confirmar" };
  return labels[value] || value || "confirmar";
}

function itemBody(item) {
  const blocks = [];
  if (item.dimensions?.length) {
    blocks.push("COTAS / INFORMAÇÕES\n" + item.dimensions.map((entry) => `${entry.label}: ${entry.value} (${sourceLabel(entry.source)})`).join("\n"));
  }
  if (item.quantity) {
    blocks.push(`QUANTIDADE\n${item.quantity.value} ${item.quantity.unit || "unidade"} (${sourceLabel(item.quantity.source)})`);
  }
  if (item.description?.length) blocks.push("DESCRIÇÃO\n" + item.description.map((line) => `• ${line}`).join("\n"));
  if (item.construction?.length) blocks.push("CONSTRUÇÃO\n" + item.construction.map((line) => `• ${line}`).join("\n"));
  if (item.materials_finishes?.length) blocks.push("MATERIAIS / ACABAMENTOS\n" + item.materials_finishes.map((line) => `• ${line}`).join("\n"));
  if (item.integrated_systems?.length) blocks.push("SISTEMAS INTEGRADOS\n" + item.integrated_systems.map((line) => `• ${line}`).join("\n"));
  if (item.access_maintenance?.length) blocks.push("ACESSO / MANUTENÇÃO\n" + item.access_maintenance.map((line) => `• ${line}`).join("\n"));
  if (item.installation_notes?.length) blocks.push("MONTAGEM / INTERFACES\n" + item.installation_notes.map((line) => `• ${line}`).join("\n"));
  if (item.safety_notes?.length) blocks.push("SEGURANÇA / VALIDAÇÃO\n" + item.safety_notes.map((line) => `• ${line}`).join("\n"));
  if (item.component_schedule?.length) {
    blocks.push("QUADRO CONSOLIDADO\n" + item.component_schedule.map((entry) => {
      const quantity = entry.quantity ? ` — ${entry.quantity}` : "";
      const dimensions = entry.dimensions ? ` — ${entry.dimensions}` : "";
      const source = entry.source ? ` (${sourceLabel(entry.source)})` : "";
      return `• ${entry.item}${quantity}${dimensions}${source}`;
    }).join("\n"));
  }
  if (item.pending?.length) blocks.push("PENDÊNCIAS\n" + item.pending.map((line) => `• ${line}`).join("\n"));
  return blocks.join("\n\n");
}

function notesForItem(spec, item) {
  const sources = new Set();
  if (spec.source_model) sources.add(`Modelo: ${spec.source_model}`);
  for (const image of item.images || []) sources.add(`Imagem: ${image.path}`);
  for (const evidence of item.evidence || []) {
    sources.add(`${sourceLabel(evidence.source)}: ${evidence.claim}${evidence.locator ? ` — ${evidence.locator}` : ""}`);
  }
  return `[Sources]\n${[...sources].map((entry) => `- ${entry}`).join("\n")}\n[/Sources]`;
}

async function addItemSlide(presentation, spec, item, specDir) {
  const slide = presentation.slides.add();
  slide.background.fill = "#FFFFFF";
  const margin = 54;
  const titleTop = 38;
  const contentTop = 112;
  const contentHeight = 548;
  const imageWidth = 810;
  const gutter = 32;
  const textLeft = margin + imageWidth + gutter;
  const textWidth = 1280 - margin - textLeft;

  addText(
    slide,
    `title-${item.number}`,
    `${item.number || ""}  ${item.title || "ITEM"}`.trim(),
    { left: margin, top: titleTop, width: 804, height: 62 },
    { fontSize: 36, bold: true, color: "#1F2933" },
  );
  addText(
    slide,
    `project-${item.number}`,
    [spec.project, spec.revision].filter(Boolean).join(" — "),
    { left: 890, top: 46, width: 336, height: 30 },
    { fontSize: 16, color: "#667085", alignment: "right" },
  );

  const images = (item.images || []).slice(0, 4);
  if (!images.length) throw new Error(`Item ${item.number || "?"} has no image`);
  const imageGap = images.length > 1 ? 18 : 0;
  const grid = images.length > 2;
  const imageHeight = grid ? (contentHeight - imageGap) / 2 : images.length > 1 ? (contentHeight - imageGap) / 2 : contentHeight;
  const gridImageWidth = grid ? (imageWidth - imageGap) / 2 : imageWidth;
  for (const [index, image] of images.entries()) {
    const absolutePath = path.resolve(specDir, image.path);
    slide.images.add({
      blob: await imageBytes(absolutePath),
      contentType: contentType(absolutePath),
      alt: image.caption || `${item.title} — vista ${index + 1}`,
      fit: "contain",
      position: {
        left: margin + (grid ? (index % 2) * (gridImageWidth + imageGap) : 0),
        top: contentTop + (grid ? Math.floor(index / 2) : index) * (imageHeight + imageGap),
        width: gridImageWidth,
        height: imageHeight,
      },
    });
  }

  const body = itemBody(item);
  const bodyFont = item.body_font_size || 14;
  addText(
    slide,
    `technical-copy-${item.number}`,
    body,
    { left: textLeft, top: contentTop, width: textWidth, height: contentHeight },
    { fontSize: bodyFont, color: "#263238" },
  );
  slide.speakerNotes.textFrame.setText(notesForItem(spec, item));
  slide.speakerNotes.setVisible(false);
}

async function writeBlob(target, blob) {
  await fs.writeFile(target, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  const args = parseArgs(process.argv);
  const specPath = path.resolve(args.spec);
  const outputPath = path.resolve(args.output);
  const spec = JSON.parse((await fs.readFile(specPath, "utf8")).replace(/^\uFEFF/, ""));
  if (!Array.isArray(spec.items) || !spec.items.length) throw new Error("Specification has no items");

  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  for (const item of spec.items) await addItemSlide(presentation, spec, item, path.dirname(specPath));

  if (args["qa-dir"]) {
    const qaDir = path.resolve(args["qa-dir"]);
    await fs.mkdir(qaDir, { recursive: true });
    for (const [index, slide] of presentation.slides.items.entries()) {
      const stem = `slide-${String(index + 1).padStart(2, "0")}`;
      await writeBlob(path.join(qaDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 1 }));
      const layout = await slide.export({ format: "layout" });
      await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
    }
    await writeBlob(path.join(qaDir, "montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));
  }

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
  console.log(JSON.stringify({ output: outputPath, slides: spec.items.length }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
