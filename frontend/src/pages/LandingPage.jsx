import LandingNavbar from '../components/landing/LandingNavbar'
import HeroSection from '../components/landing/HeroSection'
import FeatureShowcase from '../components/landing/FeatureShowcase'
import AgentWorkflow from '../components/landing/AgentWorkflow'
import LearningLoop from '../components/landing/LearningLoop'
import TechHighlights from '../components/landing/TechHighlights'
import ModelSupport from '../components/landing/ModelSupport'
import FinalCTA from '../components/landing/FinalCTA'
import LandingFooter from '../components/landing/LandingFooter'
import '../components/landing/landing-vars.css'
import './LandingPage.css'

export default function LandingPage() {
  return (
    <div className="landing-page">
      <LandingNavbar />
      <main>
        <HeroSection />
        <FeatureShowcase />
        <AgentWorkflow />
        <LearningLoop />
        <TechHighlights />
        <ModelSupport />
        <FinalCTA />
      </main>
      <LandingFooter />
    </div>
  )
}
