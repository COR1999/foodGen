import Link from 'next/link';
import { ChefHat, Github, Twitter, Instagram } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Brand Column */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <ChefHat className="h-6 w-6 text-orange-500" />
              <span className="font-bold text-lg text-gray-900">ChefAI</span>
            </div>
            <p className="text-gray-500 text-sm">
              Turning ingredients into masterpieces with AI.
            </p>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase mb-4">Product</h3>
            <ul className="space-y-3">
              <li><Link href="/generate" className="text-base text-gray-500 hover:text-orange-500">Generator</Link></li>
              <li><Link href="/saved" className="text-base text-gray-500 hover:text-orange-500">My Recipes</Link></li>
            </ul>
          </div>

          {/* Support Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase mb-4">Support</h3>
            <ul className="space-y-3">
              <li><Link href="/about" className="text-base text-gray-500 hover:text-orange-500">About Us</Link></li>
              <li><Link href="/privacy" className="text-base text-gray-500 hover:text-orange-500">Privacy Policy</Link></li>
            </ul>
          </div>

          {/* Social Icons */}
          <div>
            <h3 className="text-sm font-semibold text-gray-400 tracking-wider uppercase mb-4">Follow Us</h3>
            <div className="flex space-x-6">
              <a href="#" className="text-gray-400 hover:text-orange-500">
                <Twitter className="h-6 w-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-orange-500">
                <Github className="h-6 w-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-orange-500">
                <Instagram className="h-6 w-6" />
              </a>
            </div>
          </div>
        </div>
        
        <div className="mt-8 border-t border-gray-200 pt-8 flex justify-center">
          <p className="text-base text-gray-400">
            &copy; {currentYear} ChefAI Inc. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;