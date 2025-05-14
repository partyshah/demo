import { motion } from "framer-motion";
import Link from "next/link";

import { MessageIcon } from "./icons";
import { LogoPython } from "@/app/icons";

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-20"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
        <p className="flex flex-row justify-center gap-4 items-center">
          <LogoPython size={32} />
          <span>+</span>
          <MessageIcon size={32} />
        </p>
        <h2 className="text-2xl font-semibold">Welcome to Coding Tutor</h2>
        <p>
          Your personalized coding tutor to teach you how to code through{" "}
          <span className="font-medium">guided discovery</span> and a{" "}
          <span className="font-medium">Socratic teaching approach</span>.
        </p>
        
        <div className="text-left">
          <h3 className="font-medium mb-2 text">How it works:</h3>
          <ul className="list-disc pl-6 space-y-1">
            <li><span className="font-medium">Learn by doing</span> with guided project-based milestones</li>
            <li><span className="font-medium">Get personalized guidance</span> when you're stuck</li>
          </ul>
        </div>
        
        <p className="italic text-muted-foreground">
          "“The best way to learn how to write code is to write code.”"
        </p>
      </div>
    </motion.div>
  );
};