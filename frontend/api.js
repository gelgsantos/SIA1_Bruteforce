import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000/api"; // Backend base URL

export const getUsers = async () => {
  const response = await axios.get(`${API_BASE_URL}/users`);
  return response.data;
};

export const registerUser = async (username, password) => {
  const response = await axios.post(`${API_BASE_URL}/register`, {
    username,
    password,
  });
  return response.data;
};
