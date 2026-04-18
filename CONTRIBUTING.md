# Contributing to DeepSafe

We welcome contributions of all kinds — bug fixes, new detection models, documentation, and benchmarks.

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-new-model`
3. Commit your changes: `git commit -m 'feat: add MyDetector model'`
4. Push to your branch: `git push origin feat/my-new-model`
5. Open a Pull Request

## Adding a New Model

The easiest way to contribute is adding a detection model:

```bash
make add-model NAME=my_detector MEDIA_TYPE=image PORT=5008
# Then implement models/image/my_detector/detector.py
```

See [docs/adding-a-model.md](docs/adding-a-model.md) for the full guide.

## Code Style

- Python: `black` + `flake8` (run `make lint`)
- JS/React: ESLint + Prettier

## Tests

```bash
make test
```

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
