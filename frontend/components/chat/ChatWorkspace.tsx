"use client";

import { AuthRequiredCard } from "@/components/chat/AuthRequiredCard";
import { BottomComposer } from "@/components/chat/BottomComposer";
import { ChatConversation } from "@/components/chat/ChatConversation";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { MenuButton } from "@/components/chat/MenuButton";
import { useChatWorkflow } from "@/components/chat/useChatWorkflow";

export function ChatWorkspace() {
    const workflow = useChatWorkflow();

    return (
        <main className="min-h-screen bg-black text-white">
            <MenuButton onOpen={() => workflow.setDrawerOpen(true)} />

            {workflow.drawerOpen && (
                <button
                    type="button"
                    aria-label="Close menu backdrop"
                    onClick={() => workflow.setDrawerOpen(false)}
                    className="fixed inset-0 z-30 bg-black/60"
                />
            )}

            <ChatSidebar
                drawerOpen={workflow.drawerOpen}
                isLoggedIn={workflow.isLoggedIn}
                isCreatingChat={workflow.isCreatingChat}
                threadsLoading={workflow.threadsLoading}
                threads={workflow.threads}
                activeThreadId={workflow.activeThreadId}
                userEmail={workflow.userEmail}
                onClose={() => workflow.setDrawerOpen(false)}
                onQuickNewChat={workflow.handleQuickNewChat}
                onSelectThread={(threadId) => {
                    workflow.setDrawerOpen(false);
                    workflow.setActiveThreadId(threadId);
                }}
                onLogout={workflow.handleLogout}
            />

            <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 pb-36 pt-16 md:px-8 md:pb-40">
                <header className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5">
                    <h1 className="text-2xl font-bold tracking-tight text-blue-400">AI Chat Workspace</h1>
                    <p className="mt-1 text-sm text-zinc-400">Secure chat management with per-user thread history.</p>
                </header>

                {!workflow.authReady && (
                    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 text-sm text-zinc-400">Checking session...</div>
                )}

                {workflow.authReady && !workflow.isLoggedIn && <AuthRequiredCard />}

                {workflow.authReady && workflow.isLoggedIn && (
                    <ChatConversation
                        globalError={workflow.globalError}
                        activeThreadPrompt={workflow.activeThreadPrompt}
                        activeThreadId={workflow.activeThreadId}
                        activeThreadLoading={workflow.activeThreadLoading}
                        activeThreadMarkdown={workflow.activeThreadMarkdown}
                        isStreaming={workflow.isStreaming}
                        currentNode={workflow.currentNode}
                        workflowNodes={workflow.workflowNodes}
                        waitingForApproval={workflow.waitingForApproval}
                        approvalSubmitting={workflow.approvalSubmitting}
                        activeApprovalAction={workflow.activeApprovalAction}
                        criticOutput={workflow.criticOutput}
                        onApprove={() => void workflow.handleReviewDecision(true)}
                        onReject={() => void workflow.handleReviewDecision(false)}
                    />
                )}
            </section>

            {workflow.isLoggedIn && (
                <BottomComposer
                    prompt={workflow.prompt}
                    isCreatingChat={workflow.isCreatingChat}
                    disabled={Boolean(workflow.activeThreadId)}
                    disabledHint="This chat is complete. Click New Chat to start a fresh one."
                    onPromptChange={workflow.setPrompt}
                    onSubmit={workflow.handlePromptSubmit}
                />
            )}
        </main>
    );
}