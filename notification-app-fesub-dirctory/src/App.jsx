import { Routes, Route, NavLink } from "react-router-dom";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import AllNotifications from "./pages/AllNotifications.jsx";
import PriorityNotifications from "./pages/PriorityNotifications.jsx";

const navButtonStyle = ({ isActive }) => ({
  color: "#fff",
  textDecoration: "none",
  opacity: isActive ? 1 : 0.8,
});

export default function App() {
  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f4f6f8" }}>
      <AppBar position="static" color="primary" elevation={2}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ py: 1 }}>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Campus Notifications
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button component={NavLink} to="/" sx={navButtonStyle} end>
                All Notifications
              </Button>
              <Button component={NavLink} to="/priority" sx={navButtonStyle}>
                Priority Notifications
              </Button>
            </Stack>
          </Toolbar>
        </Container>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<AllNotifications />} />
          <Route path="/priority" element={<PriorityNotifications />} />
        </Routes>
      </Container>
    </Box>
  );
}
