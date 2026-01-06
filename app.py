import random

import simpy
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


def run_simulation(
    num_cashiers: int,
    sim_time: int,
    min_interarrival: int,
    max_interarrival: int,
    min_service: int,
    max_service: int,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Menjalankan simulasi antrian sederhana dan mengembalikan hasil sebagai DataFrame."""

    # Set seed agar hasil bisa direplikasi
    random.seed(random_seed)

    records = []
    env = simpy.Environment()
    cashier = simpy.Resource(env, capacity=num_cashiers)

    def service_customer(env, customer_id, cashier):
        arrival_time = env.now
        with cashier.request() as request:
            yield request
            start_service_time = env.now
            service_duration = random.randint(min_service, max_service)
            yield env.timeout(service_duration)
            finish_time = env.now

            queue_time = start_service_time - arrival_time
            system_time = finish_time - arrival_time

            records.append(
                {
                    "customer_id": customer_id,
                    "arrival_time": arrival_time,
                    "start_service": start_service_time,
                    "finish_time": finish_time,
                    "queue_time": queue_time,
                    "service_duration": service_duration,
                    "system_time": system_time,
                }
            )

    def customer_generator(env, cashier):
        i = 0
        while True:
            i += 1
            inter_arrival = random.randint(min_interarrival, max_interarrival)
            yield env.timeout(inter_arrival)
            env.process(service_customer(env, f"Customer {i}", cashier))

    env.process(customer_generator(env, cashier))
    env.run(until=sim_time)

    return pd.DataFrame(records)


def main():
    st.set_page_config(page_title="Simulasi Antrian SPBU / Kasir", layout="wide")

    st.title("Simulasi Antrian Kasir (Berbasis SimPy)")
    st.markdown(
        """
Aplikasi ini memvisualisasikan **simulasi antrian** seperti pada notebook:

- Skenario **A**: jumlah kasir tertentu (misalnya 1 kasir)  
- Skenario **B**: jumlah kasir lebih banyak (misalnya 2 kasir)  

Hasil yang ditampilkan:
- Distribusi waktu tunggu pelanggan (histogram)
- Waktu tunggu tiap pelanggan (grafik garis)
- Rata-rata waktu tunggu dan waktu di sistem
- Kesimpulan apakah penambahan kasir mengurangi waktu tunggu
"""
    )

    # Sidebar untuk parameter simulasi
    st.sidebar.header("Parameter Simulasi")

    sim_time = st.sidebar.number_input(
        "Waktu simulasi (menit)", min_value=100, max_value=10000, value=1000, step=100
    )

    st.sidebar.subheader("Jarak Kedatangan (Interarrival)")
    min_interarrival = st.sidebar.number_input(
        "Interarrival minimum (menit)", min_value=1, max_value=60, value=2
    )
    max_interarrival = st.sidebar.number_input(
        "Interarrival maksimum (menit)",
        min_value=min_interarrival,
        max_value=60,
        value=3,
    )

    st.sidebar.subheader("Waktu Layanan (Service Time)")
    min_service = st.sidebar.number_input(
        "Service minimum (menit)", min_value=1, max_value=60, value=4
    )
    max_service = st.sidebar.number_input(
        "Service maksimum (menit)", min_value=min_service, max_value=60, value=7
    )

    st.sidebar.subheader("Jumlah Kasir")
    num_cashiers_a = st.sidebar.number_input(
        "Jumlah kasir Skenario A", min_value=1, max_value=10, value=1
    )
    num_cashiers_b = st.sidebar.number_input(
        "Jumlah kasir Skenario B", min_value=1, max_value=10, value=2
    )

    random_seed = st.sidebar.number_input(
        "Random seed", min_value=0, max_value=999999, value=42, step=1
    )

    run_button = st.button("Jalankan Simulasi")

    if run_button:
        with st.spinner("Menjalankan simulasi..."):
            df_scenario_a = run_simulation(
                num_cashiers=num_cashiers_a,
                sim_time=sim_time,
                min_interarrival=min_interarrival,
                max_interarrival=max_interarrival,
                min_service=min_service,
                max_service=max_service,
                random_seed=random_seed,
            )

            df_scenario_b = run_simulation(
                num_cashiers=num_cashiers_b,
                sim_time=sim_time,
                min_interarrival=min_interarrival,
                max_interarrival=max_interarrival,
                min_service=min_service,
                max_service=max_service,
                random_seed=random_seed,
            )

        if df_scenario_a.empty or df_scenario_b.empty:
            st.error("Data simulasi kosong. Silakan coba lagi dengan parameter berbeda.")
            return

        # Tampilkan ringkasan data
        st.subheader("Ringkasan Data Simulasi")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Skenario A**")
            st.write(df_scenario_a.head())
        with col2:
            st.markdown("**Skenario B**")
            st.write(df_scenario_b.head())

        # Hitung metrik
        avg_wait_a = df_scenario_a["queue_time"].mean()
        avg_wait_b = df_scenario_b["queue_time"].mean()
        avg_system_a = df_scenario_a["system_time"].mean()
        avg_system_b = df_scenario_b["system_time"].mean()

        st.subheader("Perbandingan Performa Sistem")
        col3, col4 = st.columns(2)
        with col3:
            st.metric(
                label=f"Rata-rata waktu tunggu Skenario A ({num_cashiers_a} kasir)",
                value=f"{avg_wait_a:.2f} menit",
            )
            st.metric(
                label=f"Rata-rata waktu di sistem Skenario A ({num_cashiers_a} kasir)",
                value=f"{avg_system_a:.2f} menit",
            )
        with col4:
            st.metric(
                label=f"Rata-rata waktu tunggu Skenario B ({num_cashiers_b} kasir)",
                value=f"{avg_wait_b:.2f} menit",
            )
            st.metric(
                label=f"Rata-rata waktu di sistem Skenario B ({num_cashiers_b} kasir)",
                value=f"{avg_system_b:.2f} menit",
            )

        # Histogram waktu tunggu
        st.subheader("Distribusi Waktu Tunggu Pelanggan (Histogram)")
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.hist(
            df_scenario_a["queue_time"],
            bins=30,
            alpha=0.7,
            label=f"Skenario A ({num_cashiers_a} kasir)",
        )
        ax1.hist(
            df_scenario_b["queue_time"],
            bins=30,
            alpha=0.7,
            label=f"Skenario B ({num_cashiers_b} kasir)",
        )
        ax1.set_title("Distribusi Waktu Tunggu Pelanggan")
        ax1.set_xlabel("Waktu tunggu (menit)")
        ax1.set_ylabel("Frekuensi")
        ax1.legend()
        ax1.grid(True)
        st.pyplot(fig1)

        # Grafik waktu tunggu per pelanggan
        st.subheader("Waktu Tunggu per Pelanggan")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(
            range(1, len(df_scenario_a) + 1),
            df_scenario_a["queue_time"],
            marker="o",
            linestyle="-",
            label=f"Skenario A ({num_cashiers_a} kasir)",
        )
        ax2.plot(
            range(1, len(df_scenario_b) + 1),
            df_scenario_b["queue_time"],
            marker="x",
            linestyle="-",
            label=f"Skenario B ({num_cashiers_b} kasir)",
        )
        ax2.set_title("Waktu Tunggu per Pelanggan")
        ax2.set_xlabel("Urutan Kedatangan Pelanggan")
        ax2.set_ylabel("Waktu tunggu (menit)")
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2)

        # Kesimpulan
        st.subheader("Kesimpulan dan Rekomendasi")
        if avg_wait_b < avg_wait_a:
            st.success(
                "Penambahan kasir pada Skenario B **mengurangi waktu tunggu rata-rata**, "
                "sehingga penambahan kasir **disarankan**."
            )
        else:
            st.warning(
                "Penambahan kasir pada Skenario B **tidak memberikan perbaikan signifikan** "
                "terhadap waktu tunggu rata-rata."
            )

        st.markdown(
            """
**Catatan:**
- Karena proses kedatangan dan layanan bersifat acak, hasil simulasi dapat sedikit berbeda
  setiap kali dijalankan (tergantung nilai *random seed*).
- Anda dapat mengubah parameter di sidebar untuk menguji berbagai skenario kebijakan kasir.
"""
        )


if __name__ == "__main__":
    main()


