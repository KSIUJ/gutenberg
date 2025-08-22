# Docker configuration
## Dockerfile overview
The Dockerfile defines 3 final and some intermediate targets.
The final targets are `run_nginx`, `run_backend` and `run_celery`.
All build targets are described in comments in the Dockerfile itself.
The graph below visualizes the build-time layer dependencies.

## Targets in Dockerfile
- A solid line from `a` to `b` represents the `FROM a AS b` instruction.
- A dashed line from `a` to `b` represents `COPY --from a` as a layer of target `b`. 
```mermaid
flowchart TD
    node{{_node..._}}
    uv{{_uv:python..._}}
    nginx{{_nginx..._}}
    
    node --> build_webapp

    uv --> setup_base
    setup_base --> setup_django

    setup_django --> collect_static

    setup_django --> run_backend([run_backend])

    setup_base --> run_celery([run_celery])
    setup_django -. copy /app/backend .-> run_celery

    build_webapp -. copy /app/dist .-> collect_static
    nginx --> run_nginx([run_nginx])
    collect_static -. copy /app/staticroot .-> run_nginx([run_nginx])
```
