.PHONY: qa preflight test compile boundary clean

# Run full QA Gate (same as scripts/run-qa.py):
qa:
	python scripts/run-qa.py

# Individual checks:
preflight:
	python tools/pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks

test:
	python -m unittest discover -s pet-studio-widget/tests -v
	python -m unittest discover -s pet-studio-kit/tests -v

compile:
	python -m py_compile pet_studio_core/__init__.py
	python -m py_compile pet_studio_core/registry.py
	python -m py_compile pet_studio_core/state.py
	python -m py_compile pet-studio-widget/project_room_registry.py
	python -m py_compile pet-studio-widget/pet_studio_event_adapter.py
	python -m py_compile pet-studio-widget/set_pet_studio_state.py
	python -m py_compile pet-studio-widget/set_active_pet_studio.py
	python -m py_compile pet-studio-widget/pet_studio_widget.py
	python -m py_compile pet-studio-widget/project_room_scene.py
	python -m py_compile tools/pet_studio_preflight.py
	python -m py_compile tools/pet_studio_create_room.py
	python -m py_compile tools/pet_studio_create_qa_pack.py

boundary:
	python -c "from pet_studio_core import init_core, write_project_state, EXTERNAL_STATES; print('core OK')"

# Clean generated artifacts:
clean:
	rm -rf pet-studio-widget/project-room-*.json
	rm -rf pet-studio-widget/project-room-hook-events.jsonl
	rm -rf runs/*/qa-pack/
	rm -rf runs/pet-studio-preflight-render.png
	rm -rf tester/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
