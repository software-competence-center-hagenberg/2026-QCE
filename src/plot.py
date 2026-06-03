import plotly.express as px
import pandas as pd

def main():    
    # df = pd.read_excel("Protocol-DF-C.xlsx")
    df = pd.read_excel("Protocol-DF-BM-C.xlsx")
    df = df.sort_values(by=["Depth", "Qubits"], ascending=[True, True])
    # df["label"] = df.apply(lambda x: f"Max: {x['MAX']:.2f}<br /><br />{x['name']}<br /><br />Mean: {x['AVG']:.2f}", axis=1)
    df["label"] = df.apply(lambda x: f"{x['name']}<br />↑: {x['MAX']:.2f}<br />μ: {x['AVG']:.2f}", axis=1)
    # df["label"] = df.apply(lambda x: f"↑: {x['MAX']:.2f}<br />μ: {x['AVG']:.2f}", axis=1)
    # df["maxlabel"] = df["MAX"].apply(lambda x: f"Max: {x:.2f}")
    # df["avglabel"] = df["AVG"].apply(lambda x: f"Mean: {x:.2f}")
    df["Depth"] = df["Depth"].astype(str)
    df["Qubits"] = df["Qubits"].astype(str)
    fig = px.scatter(
        df,
        y="Qubits",
        x="Depth",
        size="AVG",
        color="AVG",
        size_max=40,
        #text="avglabel",
        range_color=[0, 1],
        color_continuous_scale=[
            (0.0, "yellow"),
            (1.0, "purple"),
        ],
        #title="Benchmark Circuits: Qwen3.6"
    )
    # fig.update_traces(textposition="bottom center")

    #fig.add_scatter(
    #    x=df["Depth"],
    #    y=df["Qubits"],
    #    mode="text",
    #    text=df["name"],
    #    textposition=df["textposition"],
    #    showlegend=False
    #)

    sizeref = fig.data[0].marker.sizeref
    fig.add_scatter(
        y=df["Qubits"],
        x=df["Depth"],
        mode="markers+text",
        # mode="markers",
        text=df["label"],          # values to show
        #textposition="middle center",
        # textposition="middle right",
        textposition=df["textposition"],
        marker=dict(
            size=df["MAX"],
            color="rgba(0,0,0,0)",
            sizeref=sizeref,
            sizemode="area",
            line=dict(
                    color="black",
                    width=2
                )
            ),
            name="MAX",
            showlegend=False
        )

    fig.update_yaxes(
        categoryorder="array",
        categoryarray=["5", "8", "10"],
        # categoryarray=["2", "3", "4", "6", "8", "10", "12"],
    )
    fig.update_layout(
        height=300,
        width=1600,
        margin=dict(t=0, b=0)
    )

    fig.update_layout({
        "plot_bgcolor": "rgba(0, 0, 0, 0)",
        "paper_bgcolor": "rgba(0, 0, 0, 0)",
    })
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        title_font_size=24,
        tickfont_size=18
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        title_font_size=24,
        tickfont_size=18
    )
    fig.update_layout(
        title_font_size=24,
        font_size=18
    )

    fig.show()

if __name__ == "__main__":
    main()