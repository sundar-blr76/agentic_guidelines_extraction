"""Internal MCP tool routes (/mcp/*) - Used by AI agents."""
from fastapi import APIRouter, HTTPException
import base64
from guidelines_agent.api.schemas.agent_schemas import (
    PlanQueryInput, PlanQueryOutput,
    QueryGuidelinesInput, 
    SummarizeInput,
    ExtractGuidelinesInput, ExtractGuidelinesOutput,
    PersistGuidelinesInput,
    StampEmbeddingInput
)
from guidelines_agent.api.schemas.common_schemas import SuccessResponse, SearchResult
from guidelines_agent.services import DocumentService, GuidelineService
from guidelines_agent.core.query_planner import generate_query_plan
from guidelines_agent.core.summarize import generate_summary
import logging
import tempfile
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp", tags=["mcp-tools"])

# Service instances  
document_service = DocumentService()
guideline_service = GuidelineService()


@router.post("/plan_query", response_model=PlanQueryOutput)
async def plan_query(input: PlanQueryInput):
    """Plan a user query into search strategy and summarization instructions."""
    logger.info(f"Planning query: {input.user_query[:100]}...")
    
    try:
        plan = generate_query_plan(input.user_query)
        
        if not plan:
            raise HTTPException(status_code=500, detail="Failed to generate query plan")
        
        return PlanQueryOutput(
            search_query=plan.get('search_query', input.user_query),
            summary_instruction=plan.get('summary_instruction', input.user_query),
            top_k=plan.get('top_k', 10)
        )
        
    except Exception as e:
        logger.error(f"Error planning query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query_guidelines")
async def query_guidelines(input: QueryGuidelinesInput):
    """Query guidelines using semantic or text search."""
    logger.info(f"Querying guidelines: {input.query_text[:50]}...")
    
    try:
        # Determine portfolio filter
        portfolio_ids = [input.portfolio_id] if input.portfolio_id else None
        
        # Perform search
        search_results = guideline_service.search_guidelines(
            query_text=input.query_text,
            portfolio_ids=portfolio_ids,
            top_k=input.top_k,
            use_semantic=True  # Default to semantic search
        )
        
        # Convert to API format
        results = [result.to_dict() for result in search_results]
        
        return SuccessResponse(
            success=True,
            data={
                "results": results,
                "total_found": len(results)
            },
            message=f"Found {len(results)} guidelines"
        )
        
    except Exception as e:
        logger.error(f"Error querying guidelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_guidelines(input: SummarizeInput):
    """Summarize guideline search results for a user question."""
    logger.info(f"Summarizing for question: {input.question[:50]}...")
    
    try:
        # Convert sources list to context string
        context = "\n\n".join(input.sources)
        
        # Generate summary
        summary = generate_summary(input.question, context)
        
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        return SuccessResponse(
            success=True,
            data={
                "summary": summary,
                "sources_count": len(input.sources)
            },
            message="Summary generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_guidelines", response_model=ExtractGuidelinesOutput)
async def extract_guidelines(input: ExtractGuidelinesInput):
    """Extract guidelines from uploaded PDF bytes."""
    logger.info(f"Extracting guidelines from document: {input.doc_name}")
    
    temp_file = None
    try:
        # Decode base64 PDF content
        try:
            pdf_bytes = base64.b64decode(input.pdf_bytes_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name
        
        # Extract guidelines
        result = document_service.extract_guidelines_from_pdf(temp_file_path)
        
        return ExtractGuidelinesOutput(
            is_valid=result.is_valid,
            validation_summary=result.validation_summary,
            guidelines=result.guidelines,
            portfolio_info=result.portfolio_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting guidelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass


@router.post("/persist_guidelines")
async def persist_guidelines(input: PersistGuidelinesInput):
    """Persist extracted guidelines to the database."""
    logger.info("Persisting extracted guidelines")
    
    try:
        # Convert the input data to our ExtractionResult format
        from guidelines_agent.models.entities import ExtractionResult
        
        extraction_result = ExtractionResult(
            is_valid=input.data.get('is_valid', True),
            validation_summary=input.data.get('validation_summary', 'Extracted guidelines'),
            guidelines=input.data.get('guidelines', []),
            portfolio_info=input.data.get('portfolio_info', {})
        )
        
        # Process the extraction (saves portfolio, document, guidelines)
        result = guideline_service.process_full_extraction(
            extraction_result, 
            doc_name=input.data.get('doc_name', 'Unknown Document')
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Persistence failed: {result['errors']}")
        
        return SuccessResponse(
            success=True,
            data={
                "doc_id": result['doc_id'],
                "portfolio_id": result['portfolio_id'],
                "guidelines_saved": result['guidelines_saved'],
                "portfolio_saved": result['portfolio_saved'],
                "document_saved": result['document_saved']
            },
            message=f"Successfully persisted {result['guidelines_saved']} guidelines"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error persisting guidelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stamp_embedding")
async def stamp_embeddings(input: StampEmbeddingInput):
    """Generate embeddings for guidelines that don't have them."""
    logger.info("Generating missing embeddings")
    
    try:
        result = guideline_service.generate_missing_embeddings(input.limit)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return SuccessResponse(
            success=True,
            data={
                "processed": result['processed'],
                "total_found": result.get('total_found', 0)
            },
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stamping embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))