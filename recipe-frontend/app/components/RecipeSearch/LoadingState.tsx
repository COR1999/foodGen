export default function LoadingState() {
  return (
    <div className="text-center py-12 bg-orange-50 rounded-2xl border-2 border-orange-200">
      <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-600 border-t-transparent mb-4"></div>
      <h3 className="text-lg font-bold text-gray-800">Finding the perfect recipe...</h3>
      <p className="text-gray-600 mt-2">Our AI chef is looking through the pantry</p>
    </div>
  );
}