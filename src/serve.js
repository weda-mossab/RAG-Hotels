const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bodyParser = require("body-parser");

const hotelRoutes = require("./routes/hotelRoutes");

const app = express();

app.use(cors());
app.use(bodyParser.json());

mongoose.connect("mongodb://localhost:27017/hotelDB", {
    useNewUrlParser: true,
    useUnifiedTopology: true,
});

app.use("/api/hotels", hotelRoutes);

const PORT = 5000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
