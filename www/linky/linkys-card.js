// @ts-nocheck
import "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.2.0/chart.min.js";

function formatDate(date){
    const d = new Date(date);
    const formatNumber = (n) => (n > 10 ? n : 0 + n.toString());

    return `${formatNumber(d.getHours())}:${formatNumber(d.getMinutes())}`;
};


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

    createChart(ctx, data, label) {
        if (!ctx || !data) {
            return;
        }
        return new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.map((e) => formatDate(e.date)),
                datasets: [
                    {
                        label,
                        data: data.map((e) => e.value),
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
    }


    set hass(hass) {

        const entityId = this.config.entity;
        this.content = hass.states[entityId];
        const { attribution, friendly_name } = this.content.attributes;
        if (this.content && this.shadowRoot) {
            this.shadowRoot.innerHTML = `
      <div 
      style="width: 100%; height: 100%; display: flex; align-items: center; padding: 16px; box-sizing: border-box; min-height: 50px;"
      >
          <canvas 
          style="width: 100%; height: auto;max-height:500px;  background-color: transparent; border-radius: 4px;"
          id="linkys-graph"></canvas>
        </div>
      `;

            const ctx = this.shadowRoot.getElementById("linkys-graph");
            const chart = this.createChart(ctx, attribution, friendly_name);

        }

    }

}
customElements.define("linkys-card", HelloWorldCard);