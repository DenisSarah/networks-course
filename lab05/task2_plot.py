from pathlib import Path

import matplotlib.pyplot as plt


F_MBIT = 15_000
SERVER_UPLOAD_MBIT = 30
PEER_DOWNLOAD_MBIT = 2
PEER_COUNTS = [10, 100, 1000]
PEER_UPLOAD_SPEEDS_MBIT = [0.3, 0.7, 2.0]
OUTPUT_PATH = Path(__file__).with_name("distribution_time.png")


def client_server_time(peer_count: int) -> float:
    return max(
        peer_count * F_MBIT / SERVER_UPLOAD_MBIT,
        F_MBIT / PEER_DOWNLOAD_MBIT,
    )


def p2p_time(peer_count: int, peer_upload_mbit: float) -> float:
    return max(
        F_MBIT / SERVER_UPLOAD_MBIT,
        F_MBIT / PEER_DOWNLOAD_MBIT,
        peer_count * F_MBIT / (SERVER_UPLOAD_MBIT + peer_count * peer_upload_mbit),
    )


def build_plot() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))

    cs_values = [client_server_time(peer_count) for peer_count in PEER_COUNTS]
    ax.plot(
        PEER_COUNTS,
        cs_values,
        marker="o",
        linewidth=2.5,
        color="#c0392b",
        label="Клиент-сервер",
    )

    colors = ["#1f77b4", "#2ca02c", "#f39c12"]
    for peer_upload_mbit, color in zip(PEER_UPLOAD_SPEEDS_MBIT, colors):
        values = [p2p_time(peer_count, peer_upload_mbit) for peer_count in PEER_COUNTS]
        ax.plot(
            PEER_COUNTS,
            values,
            marker="o",
            linewidth=2,
            color=color,
            label=f"P2P, u = {peer_upload_mbit} Мбит/с",
        )

    ax.set_xscale("log")
    ax.set_xticks(PEER_COUNTS)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("Число пиров N")
    ax.set_ylabel("Минимальное время раздачи, с")
    ax.set_title("Минимальное время раздачи файла F = 15 Гбит")
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=180)


if __name__ == "__main__":
    build_plot()
