# Convenciones de ramas

Complemento de [`commit-conventions.md`](commit-conventions.md): ese documento
cubre los mensajes de commit, este cubre los nombres de rama.

## Por qué existe este documento

`main` está protegida en GitHub y no acepta push directo — todo cambio entra
por rama + Pull Request. Si cada rama se nombra distinto (`arreglos`,
`RamaNueva`, `fix_bug_final_2`), el listado de ramas y PRs deja de decir nada
sobre qué contiene cada una, y la automatización (CI que corre distinto según
el tipo de cambio) no tiene de dónde agarrarse.

## El estándar que seguimos

Seguimos [**Conventional Branch v1.1.0**](https://conventionalbranch.org)
(licencia CC-BY-4.0), la especificación oficial inspirada en Conventional
Commits. No es una convención inventada acá: tiene gramática ABNF, regex
validador y formato legible por máquina (`spec.json`).

### Formato

```
<tipo>/<descripción>
```

El separador es siempre `/`.

### Tipos válidos

La especificación define un conjunto **cerrado** de tipos. Estos son todos:

| Tipo | Alias | Cuándo |
|---|---|---|
| `feature` | `feat` | Funcionalidad nueva |
| `bugfix` | `fix` | Corrección de un bug |
| `hotfix` | — | Corrección urgente en producción |
| `release` | — | Preparación de un release |
| `chore` | — | Tareas que no son código de producción: dependencias, **documentación**, config, tests, refactors |

Además, v1.1.0 agregó prefijos para identificar ramas generadas por agentes de IA:
`ai/` (genérico), `claude/`, `codex/`, `copilot/`, `cursor/`.

**Las ramas troncales no llevan prefijo:** `main`, `master`, `develop`.

### Reglas de nomenclatura

- **Solo minúsculas.** `feat/Login` es inválido.
- **Caracteres permitidos en la descripción:** `a-z`, `0-9`, `-`, `.`
- **Los guiones separan palabras:** `feat/agregar-campo-priority`
- **Los puntos son para versiones:** `release/v1.2.0`
- **Sin guiones bajos.** `feat/mi_rama` es inválido.
- **Sin separadores consecutivos ni al inicio/final.** `feat/--x` o `feat/x-` son inválidos.

Regex oficial validador:

```
^(?:main|master|develop|(?:feature|feat|bugfix|fix|hotfix|release|chore|ai|copilot|cursor|claude|codex)/[a-z0-9]+(?:\.[a-z0-9]+)*(?:-[a-z0-9]+(?:\.[a-z0-9]+)*)*)$
```

## La diferencia importante con los commits

Los tipos de rama y los tipos de commit **no son el mismo conjunto**, y este es
el error más fácil de cometer:

`commit-conventions.md` define 10 tipos de commit (`feat`, `fix`, `refactor`,
`test`, `docs`, `chore`, `ci`, `build`, `style`, `perf`). Conventional Branch
define solo 5 de propósito. Los tipos de commit que no existen como rama
(`docs`, `refactor`, `test`, `ci`, `build`, `style`, `perf`) van todos bajo
**`chore/`**.

Es decir: una rama `chore/` puede perfectamente contener commits `docs:`,
`test:` o `refactor:`. El tipo de rama describe el cambio a grandes rasgos; el
tipo de commit es más granular.

```
Rama:    chore/adr-iniciales
Commits: docs(constitution): agregar ADR-001 a ADR-005
         docs(claude-md): documentar carpeta adr/ en el árbol
```

## Ejemplos

```
# Funcionalidad nueva
feat/impl-agent-endpoint
feature/spec-agent-priority

# Corrección
fix/parseo-secciones-saltos-extra
bugfix/spec-path-404

# Documentación, tests, refactors, config → chore
chore/adr-iniciales
chore/branch-naming-conventions
chore/hypothesis-requirements

# Urgente en producción
hotfix/groq-timeout

# Release
release/v0.2.0
```

Inválidos y por qué:

```
docs/adr-iniciales        ← "docs" no es tipo de rama, usar chore/
Feature/login             ← mayúsculas
feat/mi_rama              ← guión bajo
feat/agregar--campo       ← guiones consecutivos
arreglos                  ← sin tipo
```

## Flujo completo

```
1. Crear la rama ANTES de escribir el primer archivo
   git checkout -b chore/adr-iniciales

2. Commitear siguiendo commit-conventions.md
   git commit -m "docs(constitution): agregar ADR-001 a ADR-005"

3. Push de la rama
   git push -u origin chore/adr-iniciales

4. Abrir el PR
   gh pr create

5. Merge (0 aprobaciones requeridas, no hay que esperar a nadie)
```

## Cómo usar esta guía con el AI

Cuando estés por empezar un cambio, podés pedirle:

> "Creá la rama para este cambio siguiendo `docs/branch-conventions.md`"

El AI elegirá el tipo según qué se va a tocar y explicará por qué —
especialmente en los casos donde el tipo de rama y el de commit difieren
(documentación → `chore/` con commits `docs:`).
