export default async function BlogThread({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Blog Thread: {id}</h1>
            <p className="text-gray-600 mb-6">This is where the blog thread content will be displayed.</p>
            {/* Blog thread content will go here */}
        </div>
    );
}