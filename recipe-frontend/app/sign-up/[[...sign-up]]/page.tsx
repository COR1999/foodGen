// app/sign-up/[[...sign-up]]/page.tsx
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="flex items-center justify-center py-12">
      <SignUp
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "shadow-lg",
            headerTitle: "text-gray-900",
            headerSubtitle: "text-gray-600",
            socialButtonsBlockButton:
              "border-gray-200 hover:bg-gray-50 text-gray-700",
            formButtonPrimary:
              "bg-orange-500 hover:bg-orange-600 text-white",
            footerActionLink: "text-orange-500 hover:text-orange-600",
          },
        }}
      />
    </div>
  );
}