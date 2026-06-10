# Blog de rimoliga

Blog personal estático en Hugo, federado con el Fediverso vía Bridgy Fed.

**Sitio:** https://blog.gabi.net.ar  
**Identidad federada:** `@blog.gabi.net.ar@blog.gabi.net.ar`  
**Feed RSS:** https://blog.gabi.net.ar/index.xml

## Flujo de publicación

1. Abrir `vault/` como bóveda en Obsidian
2. Escribir una nota en `vault/posts/`
3. Cambiar `publish: false` → `publish: true` en el frontmatter
4. "Commit and push" desde Obsidian Git (paleta de comandos)
5. GitHub Actions convierte, construye y despliega automáticamente

## Estructura

```
vault/posts/       ← fuente de verdad de los posts (editar aquí)
vault/adjuntos/    ← imágenes pegadas desde Obsidian
vault/borradores/  ← notas privadas (nunca se publican)
scripts/           ← obsidian_to_hugo.py (conversión en CI)
layouts/           ← plantillas Hugo con microformats2
static/            ← webfinger, avatar, CNAME
content/posts/     ← generado en CI, no editar ni versionar
```

## Setup inicial (una sola vez)

### 1. GitHub Pages
Settings → Pages → Source: **GitHub Actions**

### 2. DNS
Crear registro `CNAME` en tu proveedor:
```
blog.gabi.net.ar  →  rimoliga.github.io
```

### 3. Obsidian
- Abrir la carpeta `vault/` como bóveda
- Instalar plugin comunitario **Obsidian Git**
- Configurar con token de acceso personal de GitHub (permiso `repo`)
- Carpeta de adjuntos: `adjuntos/`

### 4. Bridgy Fed
- Visitar https://fed.brid.gy/web-site
- Introducir `https://blog.gabi.net.ar/` y habilitar federación

## Publicar con `publish: true`

Frontmatter mínimo de una nota:

```yaml
---
title: Mi post
date: 2026-06-10
publish: true
---
```

Las notas sin `publish: true` **nunca aparecen** en el sitio ni en el feed.

## Wikilinks e imágenes

- `[[Otra nota]]` → enlace al post si tiene `publish: true`; texto plano si no
- `![[adjuntos/imagen.png]]` → copiada a `static/img/` y enlazada correctamente
