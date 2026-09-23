import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { GuestOnly, RequireAdmin, RequireAuth } from "./components/layout/Guards";
import { PageFallback, PublicLayout, ScrollToTop } from "./components/layout/PublicLayout";
import Home from "./pages/Home";

const About = lazy(() => import("./pages/About"));
const Aduda = lazy(() => import("./pages/Aduda"));
const OurRecord = lazy(() => import("./pages/OurRecord"));
const RecordDetail = lazy(() => import("./pages/RecordDetail"));
const AreaCouncils = lazy(() => import("./pages/AreaCouncils"));
const AreaCouncilDetail = lazy(() => import("./pages/AreaCouncilDetail"));
const News = lazy(() => import("./pages/News"));
const NewsDetail = lazy(() => import("./pages/NewsDetail"));
const Events = lazy(() => import("./pages/Events"));
const EventDetail = lazy(() => import("./pages/EventDetail"));
const Community = lazy(() => import("./pages/Community"));
const DiscussionDetail = lazy(() => import("./pages/DiscussionDetail"));
const Contact = lazy(() => import("./pages/Contact"));
const SearchPage = lazy(() => import("./pages/Search"));
const Join = lazy(() => import("./pages/Join"));
const Login = lazy(() => import("./pages/Login"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const Legal = lazy(() => import("./pages/Legal"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Dashboard = lazy(() => import("./pages/member/Dashboard"));
const Notifications = lazy(() => import("./pages/member/Notifications"));
const Settings = lazy(() => import("./pages/member/Settings"));
const AdminApp = lazy(() => import("./pages/admin/AdminApp"));

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route
          path="/admin/*"
          element={
            <RequireAdmin>
              <Suspense fallback={<PageFallback />}>
                <AdminApp />
              </Suspense>
            </RequireAdmin>
          }
        />
        <Route element={<PublicLayout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="philip-aduda" element={<Aduda />} />
          <Route path="our-record" element={<OurRecord />} />
          <Route path="our-record/:slug" element={<RecordDetail />} />
          <Route path="area-councils" element={<AreaCouncils />} />
          <Route path="area-councils/:slug" element={<AreaCouncilDetail />} />
          <Route path="news" element={<News />} />
          <Route path="news/:slug" element={<NewsDetail />} />
          <Route path="events" element={<Events />} />
          <Route path="events/:slug" element={<EventDetail />} />
          <Route path="community" element={<Community />} />
          <Route path="community/:id" element={<DiscussionDetail />} />
          <Route path="contact" element={<Contact />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="join" element={<Join />} />
          <Route path="login" element={<GuestOnly><Login /></GuestOnly>} />
          <Route path="forgot-password" element={<ForgotPassword />} />
          <Route path="privacy" element={<Legal doc="privacy" />} />
          <Route path="terms" element={<Legal doc="terms" />} />
          <Route path="community-guidelines" element={<Legal doc="guidelines" />} />
          <Route path="dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="notifications" element={<RequireAuth><Notifications /></RequireAuth>} />
          <Route path="settings" element={<RequireAuth><Settings /></RequireAuth>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
