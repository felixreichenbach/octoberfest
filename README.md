# Oktoberfest Demo

## Grafana `agento11y` Installation

Install packages:

```shell
brew install grafana/grafana/agento11y
```

Configure `agento11y`:

```shell
agento11y login
```

Activate the Copilot integration:

```shell
agento11y copilot install
```

Verify the installation:

```shell
agento11y local status
agento11y doctor
```
