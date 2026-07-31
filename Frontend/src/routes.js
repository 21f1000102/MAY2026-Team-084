import { createWebHistory, createRouter } from "vue-router";
import HomePage from "./components/Home.vue";
import LoginPage from "./components/LoginPage.vue";
import RegisterPage from "./components/RegisterPage.vue";
import AssociationManager from "./components/AssociationManager.vue";
import AddAnnouncement from "./components/AddAnnouncement.vue";
import EditAnnouncement from "./components/EditAnnouncement.vue";
import Members from "./components/Members.vue";
import AddMember from "./components/AddMember.vue";
import EditMember from "./components/EditMember.vue";
import Associationcomplaint from "./components/Associationcomplaint.vue";
import ComplaintDetail from "./components/ComplaintDetail.vue";
import AddComplaint from "./components/AddComplaint.vue";
import AssociationInvoice from "./components/AssociationInvoice.vue";
import InvoiceDetail from "./components/InvoiceDetail.vue";
import TenantDashboard from "./components/TenantDashboard.vue";
import TenantComplaint from "./components/TenantComplaint.vue";
import TenantComplaintDetails from "./components/TenantComplaintDetails.vue";
import RaiseComplaint from "./components/AddComplaint.vue";

const routes = [
  {
    path: "/",
    name: "HomePage",
    component: HomePage
  },
  {
    path: "/login",
    name: "LoginPage",
    component: LoginPage
  },
  {
    path: "/register",
    name: "RegisterPage",
    component: RegisterPage
  },
  {
    path: "/associate_manager",
    redirect: "/association_manager"
  },
  {
    path: "/admin_dashboard",
    redirect: "/association_manager"
  },
  {
    path: "/association_manager",
    name: "AssociationManager",
    component: AssociationManager
  }
  ,
  {
    path: "/add-announcement",
    name: "AddAnnouncement",
    component: AddAnnouncement
  },
  {
    path: "/edit-announcement/:id",
    name: "EditAnnouncement",
    component: EditAnnouncement,
    props: true
  },
  {
    path: "/members",
    name: "Members",
    component: Members
  },
  {
    path: "/add-member",
    name: "AddMember",
    component: AddMember
  },
  {
    path: "/edit-member/:id",
    name: "EditMember",
    component: EditMember,
    props: true
  }
  ,
  {
    path: "/complaints",
    name: "Associationcomplaint",
    component: Associationcomplaint
  },
  {
    path: "/complaints/:id",
    name: "ComplaintDetail",
    component: ComplaintDetail,
    props: true
  }
  ,
  {
    path: "/add-complaint",
    name: "AddComplaint",
    component: AddComplaint
  }
  ,
  {
    path: "/invoices",
    name: "AssociationInvoice",
    component: AssociationInvoice
  }
  ,
  {
    path: "/invoices/:id/detail",
    name: "InvoiceDetail",
    component: InvoiceDetail,
    props: true
  },
  {
    path: "/tenant-dashboard",
    name: "TenantDashboard",
    component: TenantDashboard
  },
  {
    path: "/tenant-complaints",
    name: "TenantComplaint",
    component: TenantComplaint
  },
  {
    path: "/tenant-complaints/:id",
    name: "TenantComplaintDetails",
    component: TenantComplaintDetails,
    props: true
  },
  {
    path: "/raise-complaint",
    name: "RaiseComplaint",
    component: RaiseComplaint
  },
  {
    path: "/Tenant_dashboard",
    redirect: "/tenant-dashboard"
  },
  {
    path: "/tenant_dashboard",
    redirect: "/tenant-dashboard"
  },
  {
    path: "/Tenant_complaints",
    redirect: "/tenant-complaints"
  },
  {
    path: "/payments",
    redirect: "/tenant-dashboard"
  },
  {
    path: "/info",
    redirect: "/tenant-dashboard"
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;