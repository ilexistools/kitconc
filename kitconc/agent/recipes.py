# -*- coding: utf-8 -*-
"""Recipes: named, documented, parameterized pipelines.

Built-in recipes ship in ``kitconc/agent/recipes/*.json``; user recipes live in
``<workspace>/recipes/*.json`` and take precedence over built-ins with the same name. A recipe is a
pipeline (see :mod:`kitconc.agent.pipeline`) plus metadata::

    {
      "name": "glossary-candidates",          # file name and identifier
      "title": "Glossary candidates",
      "description": "What it does and when to use it.",
      "tags": ["terminology"],
      "params": {...}, "steps": [...], "output": "final",
      "interpretation": "How to read and report the results."
    }

Recipes are starting points: read one with ``recipe_show``, adapt its steps and run the variant with
``pipeline_run``, or save it with ``recipe_save``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from kitconc.agent.pipeline import ParamsArg, validate_spec
from kitconc.agent.results import ToolFailure

BUILTIN_DIR = Path(__file__).resolve().parent / "recipes"
USER_DIRNAME = "recipes"
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")

RecipeNameArg = Annotated[str, Field(description="Recipe name, as listed by recipe_list.")]


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("name", path.stem)
    return data


class RecipesMixin:
    """Mixed into KitconcTools; relies on ``self.actions`` and ``self._run_pipeline``."""

    def _user_recipe_dir(self) -> Path:
        return Path(self.actions.workspace()) / USER_DIRNAME

    def _recipes(self) -> dict[str, tuple[str, Path]]:
        found: dict[str, tuple[str, Path]] = {}
        for source, folder in (("builtin", BUILTIN_DIR), ("user", self._user_recipe_dir())):
            if folder.is_dir():
                for path in sorted(folder.glob("*.json")):
                    found[path.stem] = (source, path)
        return found

    def _recipe(self, name: str) -> tuple[dict[str, Any], str, Path]:
        recipes = self._recipes()
        if name not in recipes:
            raise ToolFailure("RECIPE_NOT_FOUND", f"Recipe not found: {name}", candidates=sorted(recipes))
        source, path = recipes[name]
        try:
            return _load(path), source, path
        except (OSError, ValueError) as exc:
            raise ToolFailure("INVALID_RECIPE", f"Cannot read recipe {path}: {exc}") from exc

    def recipe_list(
        self,
        tag: Annotated[str | None, Field(description="Only recipes with this tag (e.g. terminology, "
                                                     "comparison, lexis, quality).")] = None,
    ) -> dict[str, Any]:
        """List available recipes (built-in and the user's), with their purpose and parameters. Recipes are
        ready-made pipelines for common studies: corpus profile, word profile, corpus comparison, synonyms,
        keyword report, glossary candidates, lexical bundles, collocation entries, corpus QA."""
        items = []
        for name, (source, path) in sorted(self._recipes().items()):
            try:
                data = _load(path)
            except (OSError, ValueError):
                continue
            if tag and tag not in data.get("tags", []):
                continue
            params = {
                key: {k: v for k, v in (decl if isinstance(decl, dict) else {"default": decl}).items()
                      if k in ("type", "required", "default", "description")}
                for key, decl in (data.get("params") or {}).items()
            }
            items.append({"name": name, "title": data.get("title"), "description": data.get("description"),
                          "tags": data.get("tags", []), "params": params, "source": source})
        return {"recipes": items, "total": len(items)}

    def recipe_show(self, name: RecipeNameArg) -> dict[str, Any]:
        """Show the full JSON of a recipe (params, steps, interpretation notes). Copy and adapt it for
        pipeline_run or recipe_save."""
        data, source, path = self._recipe(name)
        return {"source": source, "path": str(path), "recipe": data}

    def recipe_run(self, name: RecipeNameArg, params: ParamsArg = None) -> dict[str, Any]:
        """Run a recipe with the given params. Returns the per-step report, all result_ids, the output and
        the recipe's interpretation notes. Use job_start(recipe=...) for large corpora."""
        data, source, _ = self._recipe(name)
        result = self._run_pipeline(data, params)
        result["recipe"] = name
        result["source"] = source
        if data.get("interpretation"):
            result["interpretation"] = data["interpretation"]
        return result

    def recipe_save(
        self,
        recipe: Annotated[dict[str, Any], Field(description="Recipe JSON: name, title, description, tags, "
                                                            "params, steps, output, interpretation.")],
        overwrite: Annotated[bool, Field(description="Replace an existing user recipe with the same name.")]
        = False,
    ) -> dict[str, Any]:
        """Save a recipe in the workspace (<workspace>/recipes/<name>.json) so it can be listed and reused.
        A user recipe with a built-in's name overrides the built-in."""
        name = str(recipe.get("name", ""))
        if not _NAME_RE.match(name):
            raise ToolFailure("INVALID_RECIPE", "Recipe 'name' must be lowercase letters, digits, '-' or '_'.")
        errors = validate_spec(recipe, self._pipeline_tools())
        if errors:
            raise ToolFailure("INVALID_RECIPE", errors[0], candidates=errors)
        folder = self._user_recipe_dir()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.json"
        if path.exists() and not overwrite:
            raise ToolFailure("ALREADY_EXISTS", f"User recipe '{name}' exists.", hint="Pass overwrite=true.")
        path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        overrides = (BUILTIN_DIR / f"{name}.json").is_file()
        return {"saved": name, "path": str(path), "overrides_builtin": overrides}
