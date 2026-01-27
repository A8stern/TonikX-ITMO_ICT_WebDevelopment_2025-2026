import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/Home.vue";
import HotelDetail from "../views/HotelDetail.vue";
import RoomTypeDetail from "../views/RoomTypeDetail.vue";
import Login from "../views/Login.vue";
import RegisterChoice from "../views/RegisterChoice.vue";
import RegisterClient from "../views/RegisterClient.vue";
import RegisterStaff from "../views/RegisterStaff.vue";
import Profile from "../views/Profile.vue";
import CleanerHome from "../views/CleanerHome.vue";
import AdminRooms from "../views/AdminRooms.vue";
import AdminCheckins from "../views/AdminCheckins.vue";
import AdminStaff from "../views/AdminStaff.vue";

const routes = [
  { path: "/", component: Home },
  { path: "/hotels/:id", component: HotelDetail },
  { path: "/hotels/:hotelId/types/:typeId", component: RoomTypeDetail },

  { path: "/login", component: Login },
  { path: "/register", component: RegisterChoice },
  { path: "/register/client", component: RegisterClient },
  { path: "/register/staff", component: RegisterStaff },

  { path: "/profile", component: Profile },

  { path: "/cleaner", component: CleanerHome },


  { path: "/admin/rooms", component: AdminRooms },
  { path: "/admin/checkins", component: AdminCheckins },
  { path: "/admin/staff", component: AdminStaff },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});