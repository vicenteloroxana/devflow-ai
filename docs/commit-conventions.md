# Convenciones de Commit — Conventional Commits

> Referencia independiente basada en la especificación oficial:
> https://www.conventionalcommits.org/en/v1.0.0/
>
> Para nombres de **rama**, ver [`branch-conventions.md`](branch-conventions.md).
> Los tipos de rama son un conjunto más chico que los de commit: `docs`,
> `refactor`, `test`, `ci`, `build`, `style` y `perf` existen como tipo de
> commit pero no de rama (van bajo `chore/`).

## Por qué existen estas convenciones

Un historial de commits bien formateado permite:
- Entender qué cambió y por qué sin leer el código
- Generar changelogs automáticamente
- Detectar breaking changes de forma mecánica
- Navegar la historia del proyecto meses después

Sin convenciones, el historial se llena de mensajes como "fix", "wip",
"cambios", "arreglé el bug" — que no le dicen nada a nadie, incluyendo
a vos mismo en 3 meses.

---

## Formato del mensaje

```
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer opcional]
```

### Reglas del formato

- **`<tipo>`**: obligatorio — clasifica el cambio (ver tabla abajo)
- **`(<scope>)`**: opcional — el módulo o área afectada, entre paréntesis
- **`<descripción>`**: obligatorio — en imperativo, minúsculas, sin punto final
- **Cuerpo**: opcional — explica el *por qué*, no el *qué* (el código muestra el qué)
- **Footer**: opcional — para breaking changes o referencias a issues

### La descripción va en imperativo

❌ `agregué el endpoint de generación`   ← pasado, primera persona
❌ `se agrega el endpoint de generación` ← pasado impersonal
✅ `agregar endpoint de generación`      ← imperativo (como una orden al repo)

> La convención oficial usa inglés, pero lo importante es ser consistente
> dentro del equipo. Este proyecto usa español.

---

## Los tipos — cuándo usar cada uno

### `feat` — Nueva funcionalidad

**Cuándo:** el usuario o sistema que consume tu código gana una
capacidad que antes no existía.

**La pregunta clave:** ¿puede alguien hacer algo nuevo que antes no
podía? Si sí → `feat`.

```
feat(spec-agent): agregar campo priority a SpecRequest
feat(impl-agent): inferir target_file desde sección Contexto técnico
```

**Error común:** usar `feat` cuando agregás un método interno o
refactorizás. Si el comportamiento observable no cambia, no es `feat`.

---

### `fix` — Corrección de bug

**Cuándo:** algo estaba funcionando mal (comportamiento no intencional)
y ahora funciona correctamente.

**La pregunta clave:** ¿había algo roto? Si sí → `fix`.

```
fix(spec-agent): corregir parseo de secciones cuando el LLM agrega saltos extra
fix(impl-agent): retornar 404 cuando spec_path no existe en lugar de 500
```

**Error común:** usar `fix` para cambios de comportamiento intencionales.
Si el comportamiento anterior era el diseñado y lo estás cambiando
intencionalmente, es `feat` o `refactor`, no `fix`.

---

### `refactor` — Reorganización sin cambio de comportamiento

**Cuándo:** el código hace exactamente lo mismo de antes, pero está
mejor organizado, más legible, o eliminaste duplicación.

**La pregunta clave:** ¿el comportamiento observable cambió? Si no
cambió nada desde afuera → `refactor`.

```
refactor(impl-agent): extraer infer_target() de generate_code()
refactor(spec-agent): renombrar variables para mayor claridad
```

**Error común:** confundirlo con `feat` porque "agregué un método".
Si ese método no expone nueva funcionalidad al exterior, es `refactor`.

**Regla mental:** si los tests existentes siguen pasando sin modificarse,
probablemente es `refactor`. Si tuviste que cambiar o agregar tests, el
comportamiento cambió.

---

### `docs` — Solo documentación

**Cuándo:** solo cambiaste archivos `.md`, comentarios, docstrings o
READMEs. Cero cambios en código de producción.

```
docs(constitution): agregar sección de cuándo corren los tests
docs(impl-agent): actualizar docstring de write_file()
```

**Error común:** usar `docs` cuando también modificaste código. Si el
commit toca código Y documentación, el tipo lo define el código
(`feat`, `fix`, `refactor`).

---

### `test` — Solo tests

**Cuándo:** solo agregaste, modificaste o corregiste tests. Cero
cambios en código de producción.

```
test(impl-agent): agregar property-based tests con hypothesis
test(spec-agent): cubrir caso de LLM con respuesta malformada
```

**Error común:** olvidarse de este tipo y usar `feat` o `fix` cuando
el commit solo agrega tests. Los tests son ciudadanos de primera clase
— merecen su propio tipo.

---

### `chore` — Mantenimiento sin impacto en producción ni tests

**Cuándo:** tareas de mantenimiento que no cambian el comportamiento
del sistema ni los tests. Típicamente: actualizar dependencias,
configuración de herramientas, archivos de entorno.

```
chore: agregar hypothesis a requirements.txt
chore: actualizar .gitignore para excluir .hypothesis/
```

**Error común:** usarlo como cajón de sastre para todo lo que no sabés
clasificar. Si dudás entre `chore` y otro tipo, el otro tipo
probablemente es más correcto.

---

### `perf` — Mejora de performance

**Cuándo:** el comportamiento observable no cambia, pero el sistema
es más rápido, usa menos memoria, o escala mejor. Requiere evidencia
(benchmark, profiling).

```
perf(spec-agent): cachear contexto del CLAUDE.md en lugar de leerlo por request
```

**Error común:** usarlo sin evidencia de que realmente mejoró algo.
Una optimización sin benchmark es un `refactor`.

---

### `style` — Solo formato

**Cuándo:** cambios puramente cosméticos que no afectan la lógica:
espacios, indentación, comillas, comas, orden de imports. Lo que
hace un formatter automático.

```
style: aplicar formato black a spec_agent/service.py
```

**Error común:** confundirlo con `refactor`. `style` es lo que hace
un formatter automático. `refactor` implica decisiones de diseño.

---

### `ci` — Pipelines y workflows

**Cuándo:** solo cambiaste archivos en `.github/workflows/` u otros
sistemas de CI/CD.

```
ci: agregar job de pytest al pipeline de PR
ci: configurar caché de dependencias en GitHub Actions
```

---

### `build` — Sistema de build y dependencias externas

**Cuándo:** cambios en el sistema de build, Dockerfile, docker-compose,
o dependencias del proyecto.

```
build: actualizar imagen base de Python a 3.12-slim
build(docker): separar stage de desarrollo y producción en agents/Dockerfile
```

---

## Breaking changes

Un breaking change es un cambio que rompe la compatibilidad — alguien
que usaba tu API o interfaz tendrá que modificar su código.

### Opción 1 — `!` después del tipo (forma corta)
```
feat!: cambiar formato de SpecResponse — assumptions pasa de string a list[str]
```

### Opción 2 — footer `BREAKING CHANGE:` (forma explicativa)
```
feat(spec-agent): cambiar formato de SpecResponse

BREAKING CHANGE: el campo assumptions era string, ahora es list[str].
Todo caller que leía assumptions como string debe actualizar su código.
```

**Regla:** si alguien que consume tu código tiene que cambiar algo en
su código por tu commit → es breaking change. Marcarlo es un acto de
respeto hacia los demás (y hacia vos mismo en el futuro).

---

## Scope — el módulo afectado

El scope es opcional pero muy útil en proyectos con múltiples módulos.

**Valores recomendados para este proyecto:**

| Scope | Qué cubre |
|---|---|
| `spec-agent` | `src/agents/spec_agent/` |
| `impl-agent` | `src/agents/impl_agent/` |
| `review-agent` | `src/agents/review_agent/` |
| `eval-agent` | `src/agents/eval_agent/` |
| `api` | `src/DevFlowAI/DevFlowAI.API/` |
| `domain` | `src/DevFlowAI/DevFlowAI.Domain/` |
| `infra` | `src/DevFlowAI/DevFlowAI.Infrastructure/` |
| `constitution` | `specs/constitution/` |
| `terraform` | `terraform/` |
| `docker` | Dockerfiles o docker-compose |

Si el cambio toca múltiples módulos, omitir el scope es mejor que
inventar uno que no representa bien el alcance.

---

## Árbol de decisión — cómo elegir el tipo

Ante la duda, seguí este árbol de arriba hacia abajo:

```
¿El comportamiento observable cambió?
├── Sí
│   ├── ¿Era un bug (comportamiento no intencional)?   → fix
│   └── ¿Es funcionalidad nueva o cambio intencional?  → feat
│       └── ¿Rompe compatibilidad hacia atrás?          → feat! + BREAKING CHANGE
└── No
    ├── ¿Solo reorganizaste/limpiaste código?           → refactor
    ├── ¿Solo cambiaste formato (linter/formatter)?     → style
    ├── ¿Solo cambiaste tests?                          → test
    ├── ¿Solo cambiaste documentación?                  → docs
    ├── ¿Solo cambiaste CI/CD?                          → ci
    ├── ¿Solo cambiaste build/Docker/deps?              → build
    ├── ¿Mejoró la velocidad (con evidencia)?           → perf
    └── ¿Mantenimiento sin otra categoría?              → chore
```

---

## Ejemplos completos del proyecto

```bash
# Nueva funcionalidad
feat(spec-agent): agregar endpoint POST /api/agents/spec/generate

# Bug corregido
fix(impl-agent): retornar 409 en lugar de 500 cuando archivo existe sin overwrite

# Reorganización interna
refactor(spec-agent): extraer parseo de secciones a parse_sections()

# Solo tests
test(impl-agent): agregar property-based tests con hypothesis para write_file()

# Solo documentación
docs(constitution): documentar cuándo corren los tests en el flujo SDD

# Dependencia nueva
chore: agregar hypothesis a src/agents/requirements.txt

# CI
ci: agregar ejecución de pytest en pipeline de PR

# Docker
build(docker): separar stage de desarrollo y producción en agents/Dockerfile

# Breaking change
feat!: cambiar ImplResponse.notes de str a list[str]
```

---

## Cómo usar esta guía con el AI

Cuando estés por hacer un commit, podés pedirle al AI:

> "Generá un commit para los cambios staged siguiendo
> `docs/commit-conventions.md`"

El AI leerá los cambios, aplicará el árbol de decisión de esta guía,
y explicará por qué eligió el tipo — para que puedas validarlo y
aprender el criterio, no solo copiar el resultado.
