# Linky Home Assistant Integration

This integration allows you to monitor your electricity consumption using the Linky smart meter in Home Assistant. It leverages the API provided by [Conso Boris](https://conso.boris.sh) to retrieve consumption data.

Linky Home Assistant Integration is not affiliated with Enedis or the Linky smart meter.


Please note that the data retrieved from the API is typically available one day behind and it's not possible to fetch the current day's data.

## Configuration

1. Copy the contents of `configuration.yaml` and add it to your Home Assistant configuration file.

    ```yaml
    linky:
      api_key: !secret linky.api_key
      point_id: !secret linky.point_id
      email: !secret linky.email
    ```

2. Copy the contents of `secrets.yaml` and add it to your Home Assistant secrets file.

    ```yaml
    linky.api_key: Your secret Key
    linky.point_id: Your PMR
    linky.email: Your email
    ```

3. Include the Linky resources in your Home Assistant resources.

    ```yaml
    resources:
      - url: /local/linky/linkys-card.js
        type: module
    ```

4. Add the Linky entities to your Lovelace dashboard.

    ```yaml
    card:
      type: entities
      entities:
        - entity: sensor.linky_energy
        - entity: sensor.linky_energy_month
      state_color: false
      title: Linky
      footer:
        type: custom:linkys-card
        entity: sensor.linky_energy_hours
    ```
## Credits

The Linky integration is based on the [conso.boris.sh API](
  https://conso.boris.sh)
