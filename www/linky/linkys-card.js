"use strict";
class HelloWorldCard extends HTMLElement {
    config;
    content;
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
    }
    setConfig(config) {
        this.config = config;
    }
    set hass(hass) {
        const entityId = this.config.entity;
        const state = hass.states[entityId];
        const { attribution, friendly_name } = state.attributes;
        if (!this.content && this.shadowRoot) {
            this.shadowRoot.innerHTML = `
      <div 
      style="width: 100%; height: 100%; display: flex; align-items: center; padding: 16px; box-sizing: border-box; min-height: 50px;"
      
      >
          <canvas 
          style="width: 100%; height: auto;max-height:500px;  background-color: #FFF; border-radius: 4px;"
          id="linkys-graph"></canvas>
        </div>
      `;
            const ctx = this.shadowRoot.getElementById("linkys-graph");
            if (!ctx)
                return;
            // @ts-ignore
            import(
            // @ts-ignore
            "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.min.js")
                .then((e) => {
                console.log(attribution);
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: attribution.map((e) => new Date(e.date).getHours() +
                            "h" +
                            new Date(e.date).getMinutes()),
                        datasets: [
                            {
                                label: "Watts",
                                data: attribution.map((e) => e.value),
                                borderWidth: 1,
                                backgroundColor: "rgba(255, 99, 132, 0.8)",
                                borderColor: "rgba(255, 99, 132, 1)",
                            },
                        ],
                    },
                    options: {
                        scales: {
                            // @ts-ignore
                            y: {
                                beginAtZero: true,
                            },
                        },
                    },
                });
            })
                .catch((error) => console.error(error));
            this.content = true;
        }
    }
}
customElements.define("linkys-card", HelloWorldCard);
