import { useEffect, useState } from "react";
import { ResponsiveLine } from "@nivo/line";
import { animaisApi } from "../api";
import { Box, Paper, Typography } from "@mui/material";

export default function AdoptionChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [yTicks, setYTicks] = useState([0, 1]); // ticks inteiros para o eixo Y

  const primaryColor = "#6366F1";

  useEffect(() => {
    async function load() {
      try {
        const resp = await animaisApi.adoptionMetrics(7);

        if (resp?.days) {
          // transforma YYYY-MM-DD -> DD/MM e captura máximo para ticks inteiros
          const series = resp.days.map((d) => {
            const dayStr = String(d.day || ""); 
            const dd = dayStr.slice(8, 10);
            const mm = dayStr.slice(5, 7);
            const label = dd && mm ? `${dd}/${mm}` : dayStr;
            return { x: label, y: Number(d.count || 0) };
          });

          const maxCount = Math.max(0, ...resp.days.map((d) => Number(d.count || 0)));
          const maxTick = Math.max(1, Math.ceil(maxCount)); 
          const ticks = Array.from({ length: maxTick + 1 }, (_, i) => i);

          setData([
            {
              id: "Adoções",
              color: primaryColor,
              data: series,
            },
          ]);
          setYTicks(ticks);
        } else {
          // fallback vazio
          setData([
            {
              id: "Adoções",
              color: primaryColor,
              data: [],
            },
          ]);
          setYTicks([0, 1]);
        }
      } catch (e) {
        console.error("Erro carregando métricas:", e);
        setData([
          {
            id: "Adoções",
            color: primaryColor,
            data: [],
          },
        ]);
        setYTicks([0, 1]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: "1.2rem",
        p: 3,
        boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
        border: "1px solid rgba(15,23,42,0.04)",
        height: 350,
      }}
    >
      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 700,
          color: "#1f2937",
        }}
      >
        Adoções realizadas nos últimos 7 dias 🤩
      </Typography>

      <Box sx={{ height: 260 }}>
        {!loading && (
          <ResponsiveLine
            data={data}
            margin={{ top: 20, right: 20, bottom: 40, left: 60 }}
            xScale={{ type: "point" }}
            yScale={{ type: "linear", min: 0, max: "auto" }}
            colors={[primaryColor]}
            lineWidth={3}
            pointSize={10}
            pointColor="#ffffff"
            pointBorderWidth={3}
            pointBorderColor={primaryColor}
            enableArea={true}
            areaOpacity={0.12}
            useMesh={true}
            curve="monotoneX"
            enableGridX={false}
            enableGridY={false}
            theme={{
              textColor: "#475569",
              axis: {
                ticks: {
                  text: {
                    fontSize: 12,
                    fill: "#475569",
                  },
                },
                legend: {
                  text: {
                    fontSize: 12,
                    fill: "#475569",
                  },
                },
              },
            }}
            axisBottom={{
              tickRotation: 0,
              tickSize: 8,
              legend: "Dia",
              legendOffset: 32,
              legendPosition: "middle",
            }}
            axisLeft={{
              tickSize: 6,
              tickValues: yTicks,
              legend: "Adoções",
              legendOffset: -50,
              legendPosition: "middle",
              format: (v) => String(v), 
            }}
            lineOpacity={1}
            enablePoints={true}
            tooltip={({ point }) => (
              <div style={{ background: "#fff", padding: 8, borderRadius: 6, boxShadow: "0 6px 18px rgba(0,0,0,0.08)" }}>
                <strong style={{ color: primaryColor }}>{point.data.xFormatted}</strong>
                <div style={{ color: "#374151" }}>{point.data.yFormatted} adoção{Number(point.data.y) !== 1 ? "es" : ""}</div>
              </div>
            )}
          />
        )}
      </Box>
    </Paper>
  );
}
