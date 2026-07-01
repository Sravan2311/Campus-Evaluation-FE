import { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Slider from "@mui/material/Slider";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";

function score(item) {
  const placement = { banner: 5, alert: 4, email: 3, message: 2, summary: 1 }[item.placement] || 1;
  const result = { success: 4, warning: 3, info: 2, fail: 1 }[item.result] || 2;
  const event = { deadline: 5, emergency: 4, meeting: 3, reminder: 2, social: 1 }[item.event] || 1;
  const ageHr = Math.max((Date.now() - new Date(item.timestamp)) / 3600000, 0);
  return placement * 0.35 + result * 0.25 + event * 0.25 + 1.5 / (1 + ageHr);
}

function statusChip(read) {
  return read ? (
    <Chip label="Viewed" color="success" size="small" />
  ) : (
    <Chip label="New" color="primary" size="small" />
  );
}

export default function PriorityNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch(`http://4.224.186.213/evaluation-service/notifications?limit=${limit}&page=1`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load notifications");
        return res.json();
      })
      .then((data) => setNotifications(data || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [limit]);

  const topNotifications = [...notifications]
    .sort((a, b) => score(b) - score(a))
    .slice(0, limit);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 2, mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Priority Notifications
          </Typography>
          <Typography variant="body1" sx={{ color: "text.secondary" }}>
            Prioritized top notifications with unread/new state highlighted.
          </Typography>
        </Box>
        <Box sx={{ width: 240 }}>
          <Typography gutterBottom>Top n notifications</Typography>
          <Slider
            value={limit}
            min={5}
            max={20}
            step={1}
            valueLabelDisplay="auto"
            onChange={(e, value) => setLimit(value)}
          />
        </Box>
      </Box>
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <Grid container spacing={2}>
          {topNotifications.map((item) => (
            <Grid item xs={12} md={6} key={item.id}>
              <Card component={Paper} elevation={3}>
                <CardContent>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                    <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
                      {item.placement} • {item.event}
                    </Typography>
                    {statusChip(item.read)}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {item.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
                    {item.result} • {new Date(item.timestamp).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    Priority score: {score(item).toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
