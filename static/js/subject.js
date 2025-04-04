$(document).ready(function(){		
	$('#addSubject').click(function(){
		$('#subjectModal').modal('show');
		$('#subjectForm')[0].reset();		
		$('.modal-title').html("<i class='fa fa-plus'></i> Add Subject");
		$('#action').val('addSubject');
		$('#save').val('Save');
	});	
});